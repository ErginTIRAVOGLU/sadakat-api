from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.businesses.models import BusinessUser
from app.campaign_memberships.models import CampaignMembership
from app.campaigns.models import Campaign
from app.common.enums import (
    CampaignMembershipStatus,
    QRSessionStatus,
    TransactionType,
)
from app.core.security import generate_qr_token, hash_qr_token
from app.qr_sessions.models import QRSession
from app.stamps.models import Stamp
from app.transactions.models import Transaction


QR_SESSION_EXPIRE_MINUTES = 1


async def create_qr_session(
    db: AsyncSession,
    customer_id,
) -> tuple[QRSession, str]:
    now = datetime.now(timezone.utc)

    # Expire any existing active QR sessions for this customer.
    result = await db.execute(
        select(QRSession).where(
            QRSession.customer_id == customer_id,
            QRSession.status == QRSessionStatus.ACTIVE,
        )
    )

    active_sessions = result.scalars().all()

    for session in active_sessions:
        session.status = QRSessionStatus.EXPIRED

    token = generate_qr_token()
    token_hash = hash_qr_token(token)

    expires_at = now + timedelta(
        minutes=QR_SESSION_EXPIRE_MINUTES,
    )

    qr_session = QRSession(
        customer_id=customer_id,
        token_hash=token_hash,
        expires_at=expires_at,
        status=QRSessionStatus.ACTIVE,
    )

    db.add(qr_session)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(qr_session)

    return qr_session, token

async def scan_qr_session(
    db: AsyncSession,
    token: str,
    campaign_id,
    business_user: BusinessUser,
) -> tuple[QRSession, Stamp, int]:
    now = datetime.now(timezone.utc)
    token_hash = hash_qr_token(token)

    result = await db.execute(
        select(QRSession)
        .options(selectinload(QRSession.customer))
        .where(
            QRSession.token_hash == token_hash,
        )
    )

    qr_session = result.scalar_one_or_none()

    if qr_session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="QR session not found",
        )

    if qr_session.status != QRSessionStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="QR session is no longer active",
        )

    if qr_session.expires_at <= now:
        qr_session.status = QRSessionStatus.EXPIRED

        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="QR session has expired",
        )

    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
            Campaign.business_id == business_user.business_id,
            Campaign.deleted_at.is_(None),
        )
    )

    campaign = result.scalar_one_or_none()

    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    if not campaign.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign is not active",
        )

    result = await db.execute(
        select(CampaignMembership).where(
            CampaignMembership.campaign_id == campaign.id,
            CampaignMembership.customer_id == qr_session.customer_id,
        )
    )

    membership = result.scalar_one_or_none()

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer is not a member of this campaign",
        )

    if membership.status != CampaignMembershipStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign membership is not active",
        )

    stamp = Stamp(
        campaign_membership_id=membership.id,
        qr_session_id=qr_session.id,
        business_user_id=business_user.id,
    )

    db.add(stamp)

    qr_session.status = QRSessionStatus.USED
    qr_session.used_at = now
    qr_session.business_id = business_user.business_id

    await db.flush()

    transaction = Transaction(
        user_id=qr_session.customer.user_id,
        business_id=business_user.business_id,
        type=TransactionType.STAMP_EARNED,
        reference_id=stamp.id,
        details={
            "campaign_id": str(campaign.id),
            "campaign_name": campaign.name,
        },
    )

    db.add(transaction)

    result = await db.execute(
        select(func.count(Stamp.id)).where(
            Stamp.campaign_membership_id == membership.id,
        )
    )

    stamp_count = result.scalar_one()

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(stamp)
    await db.refresh(qr_session)

    return qr_session, stamp, stamp_count