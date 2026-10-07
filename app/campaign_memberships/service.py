from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.campaign_memberships.models import CampaignMembership
from app.campaigns.models import Campaign
from app.common.enums import CampaignMembershipStatus, TransactionType
from app.transactions.models import Transaction
from app.users.models import CustomerProfile


async def join_campaign(
    db: AsyncSession,
    customer: CustomerProfile,
    campaign_id: UUID,
) -> CampaignMembership:
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == campaign_id,
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

    now = datetime.now(timezone.utc)

    if campaign.start_date is not None and now < campaign.start_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign has not started yet",
        )

    if campaign.end_date is not None and now > campaign.end_date:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign has already ended",
        )

    result = await db.execute(
        select(CampaignMembership).where(
            CampaignMembership.campaign_id == campaign.id,
            CampaignMembership.customer_id == customer.id,
        )
    )
    membership = result.scalar_one_or_none()

    if membership is not None:
        if membership.status == CampaignMembershipStatus.ACTIVE:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer is already a member of this campaign",
            )

        if membership.status == CampaignMembershipStatus.COMPLETED:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Customer has already completed this campaign",
            )

        membership.status = CampaignMembershipStatus.ACTIVE
        membership.joined_at = now
        membership.completed_at = None
    else:
        membership = CampaignMembership(
            campaign_id=campaign.id,
            customer_id=customer.id,
            status=CampaignMembershipStatus.ACTIVE,
            joined_at=now,
        )
        db.add(membership)

    await db.flush()

    transaction = Transaction(
        user_id=customer.user_id,
        business_id=campaign.business_id,
        type=TransactionType.CAMPAIGN_JOINED,
        reference_id=campaign.id,
        details={
            "campaign_name": campaign.name,
        },
    )

    db.add(transaction)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(membership)

    return membership