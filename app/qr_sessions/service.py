from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.businesses.models import BusinessUser
from app.campaign_memberships.models import CampaignMembership
from app.campaigns.models import Campaign
from app.common.enums import (
    CampaignMembershipStatus,
    CustomerRewardStatus,
    LoyaltyCardStatus,
    QRSessionStatus,
    TransactionType,
)
from app.core.security import generate_qr_token, hash_qr_token
from app.customer_rewards.models import CustomerReward
from app.loyalty_cards.models import LoyaltyCard
from app.qr_sessions.models import QRSession
from app.stamps.models import Stamp
from app.transactions.models import Transaction


QR_SESSION_EXPIRE_MINUTES = 5


def is_campaign_active(
    campaign: Campaign,
    now: datetime,
) -> bool:
    if not campaign.is_active:
        return False

    if campaign.start_date is not None and now < campaign.start_date:
        return False

    if campaign.end_date is not None and now >= campaign.end_date:
        return False

    return True


async def create_qr_session(
    db: AsyncSession,
    customer_id,
) -> tuple[QRSession, str]:
    now = datetime.now(timezone.utc)

    # Expire the customer's existing active QR sessions.
    result = await db.execute(
        select(QRSession)
        .where(
            QRSession.customer_id == customer_id,
            QRSession.status == QRSessionStatus.ACTIVE,
        )
        .with_for_update()
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

    # ---------------------------------------------------------
    # 1. Find and lock QR session
    # ---------------------------------------------------------

    result = await db.execute(
        select(QRSession)
        .options(
            selectinload(QRSession.customer),
        )
        .where(
            QRSession.token_hash == token_hash,
        )
        .with_for_update()
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

    # ---------------------------------------------------------
    # 2. Load campaign
    # ---------------------------------------------------------

    result = await db.execute(
        select(Campaign)
        .options(
            selectinload(Campaign.reward),
        )
        .where(
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

    # ---------------------------------------------------------
    # 3. Campaign validity
    # ---------------------------------------------------------

    if not is_campaign_active(campaign, now):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign is not active or has expired",
        )

    # ---------------------------------------------------------
    # 4. Find and lock campaign membership
    # ---------------------------------------------------------

    result = await db.execute(
        select(CampaignMembership)
        .where(
            CampaignMembership.campaign_id == campaign.id,
            CampaignMembership.customer_id == qr_session.customer_id,
        )
        .with_for_update()
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

    # ---------------------------------------------------------
    # 5. Find current active loyalty card
    # ---------------------------------------------------------

    result = await db.execute(
        select(LoyaltyCard)
        .where(
            LoyaltyCard.campaign_membership_id == membership.id,
            LoyaltyCard.status == LoyaltyCardStatus.ACTIVE,
        )
        .order_by(
            LoyaltyCard.card_number.desc(),
        )
        .with_for_update()
    )

    loyalty_card = result.scalar_one_or_none()

    # Normally every membership should already have a card.
    # This also makes the service resilient for existing data.
    if loyalty_card is None:
        result = await db.execute(
            select(LoyaltyCard.card_number)
            .where(
                LoyaltyCard.campaign_membership_id == membership.id,
            )
            .order_by(
                LoyaltyCard.card_number.desc(),
            )
            .limit(1)
            .with_for_update()
        )

        last_card_number = result.scalar_one_or_none()

        next_card_number = (
            last_card_number + 1
            if last_card_number is not None
            else 1
        )

        loyalty_card = LoyaltyCard(
            campaign_membership_id=membership.id,
            card_number=next_card_number,
            stamp_count=0,
            status=LoyaltyCardStatus.ACTIVE,
        )

        db.add(loyalty_card)

        await db.flush()

    # ---------------------------------------------------------
    # 6. Make sure the card is not already complete
    # ---------------------------------------------------------

    if loyalty_card.stamp_count >= campaign.stamp_target:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Loyalty card is already completed",
        )

    # ---------------------------------------------------------
    # 7. Create stamp
    # ---------------------------------------------------------

    stamp = Stamp(
        campaign_membership_id=membership.id,
        qr_session_id=qr_session.id,
        business_user_id=business_user.id,
        loyalty_card_id=loyalty_card.id,
    )

    db.add(stamp)

    loyalty_card.stamp_count += 1

    # QR session can only be used once.
    qr_session.status = QRSessionStatus.USED
    qr_session.used_at = now
    qr_session.business_id = business_user.business_id

    await db.flush()

    # ---------------------------------------------------------
    # 8. Stamp transaction
    # ---------------------------------------------------------

    db.add(
        Transaction(
            user_id=qr_session.customer.user_id,
            business_id=business_user.business_id,
            type=TransactionType.STAMP_EARNED,
            reference_id=stamp.id,
            details={
                "campaign_id": str(campaign.id),
                "campaign_name": campaign.name,
                "loyalty_card_id": str(loyalty_card.id),
                "card_number": loyalty_card.card_number,
                "stamp_count": loyalty_card.stamp_count,
                "stamp_target": campaign.stamp_target,
            },
        )
    )

    # ---------------------------------------------------------
    # 9. Card completed?
    # ---------------------------------------------------------

    customer_reward = None

    if loyalty_card.stamp_count == campaign.stamp_target:

        loyalty_card.status = LoyaltyCardStatus.COMPLETED
        loyalty_card.completed_at = now

        # -----------------------------------------------------
        # 9.1 Get campaign reward
        # -----------------------------------------------------

        reward = campaign.reward

        if reward is None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Campaign has no reward",
            )

        if not reward.is_active:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Campaign reward is not active",
            )

        # -----------------------------------------------------
        # 9.2 Create customer's earned reward
        # -----------------------------------------------------

        customer_reward = CustomerReward(
            reward_id=reward.id,
            loyalty_card_id=loyalty_card.id,
            status=CustomerRewardStatus.AVAILABLE,
            earned_at=now,
        )

        db.add(customer_reward)

        await db.flush()

        # -----------------------------------------------------
        # 9.3 Reward earned transaction
        # -----------------------------------------------------

        db.add(
            Transaction(
                user_id=qr_session.customer.user_id,
                business_id=business_user.business_id,
                type=TransactionType.REWARD_EARNED,
                reference_id=customer_reward.id,
                details={
                    "campaign_id": str(campaign.id),
                    "campaign_name": campaign.name,
                    "reward_id": str(reward.id),
                    "reward_name": reward.name,
                    "loyalty_card_id": str(loyalty_card.id),
                    "card_number": loyalty_card.card_number,
                },
            )
        )

        # -----------------------------------------------------
        # 9.4 Create next loyalty card
        # -----------------------------------------------------

        next_card = LoyaltyCard(
            campaign_membership_id=membership.id,
            card_number=loyalty_card.card_number + 1,
            stamp_count=0,
            status=LoyaltyCardStatus.ACTIVE,
        )

        db.add(next_card)

        await db.flush()

    # ---------------------------------------------------------
    # 10. Commit everything atomically
    # ---------------------------------------------------------

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(stamp)
    await db.refresh(qr_session)

    return (
        qr_session,
        stamp,
        loyalty_card.stamp_count,
    )