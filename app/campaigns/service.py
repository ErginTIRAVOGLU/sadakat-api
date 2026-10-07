from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.businesses.models import BusinessUser
from app.campaigns.models import Campaign
from app.campaigns.schemas import CampaignCreate, CampaignUpdate


async def create_campaign(
    db: AsyncSession,
    business_user: BusinessUser,
    data: CampaignCreate,
) -> Campaign:
    if (
        data.start_date is not None
        and data.end_date is not None
        and data.end_date <= data.start_date
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date",
        )

    campaign = Campaign(
        business_id=business_user.business_id,
        name=data.name,
        description=data.description,
        image_url=data.image_url,
        stamp_target=data.stamp_target,
        start_date=data.start_date,
        end_date=data.end_date,
        is_active=True,
    )

    db.add(campaign)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(campaign)

    return campaign

async def get_business_campaigns(
    db: AsyncSession,
    business_id,
) -> list[Campaign]:
    result = await db.execute(
        select(Campaign)
        .where(
            Campaign.business_id == business_id,
            Campaign.deleted_at.is_(None),
        )
        .order_by(Campaign.created_at.desc())
    )

    return list(result.scalars().all())


async def get_active_campaigns(
    db: AsyncSession,
) -> list[Campaign]:
    result = await db.execute(
        select(Campaign)
        .where(
            Campaign.is_active.is_(True),
            Campaign.deleted_at.is_(None),
        )
        .order_by(Campaign.created_at.desc())
    )

    return list(result.scalars().all())

async def get_campaign_by_id(
    db: AsyncSession,
    campaign_id: UUID,
) -> Campaign:
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

    return campaign


async def update_campaign(
    db: AsyncSession,
    campaign: Campaign,
    data: CampaignUpdate,
) -> Campaign:
    update_data = data.model_dump(exclude_unset=True)

    new_start_date = update_data.get(
        "start_date",
        campaign.start_date,
    )
    new_end_date = update_data.get(
        "end_date",
        campaign.end_date,
    )

    if (
        new_start_date is not None
        and new_end_date is not None
        and new_end_date <= new_start_date
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="End date must be after start date",
        )

    for field, value in update_data.items():
        setattr(campaign, field, value)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(campaign)

    return campaign


async def delete_campaign(
    db: AsyncSession,
    campaign: Campaign,
) -> None:
    campaign.deleted_at = datetime.now(timezone.utc)
    campaign.is_active = False

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    
def is_campaign_active(
    campaign: Campaign,
    now: datetime | None = None,
) -> bool:
    if now is None:
        now = datetime.now(timezone.utc)

    if not campaign.is_active:
        return False

    if campaign.start_date is not None and now < campaign.start_date:
        return False

    if campaign.end_date is not None and now >= campaign.end_date:
        return False

    return True