from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.businesses.models import BusinessUser
from app.campaigns.models import Campaign
from app.customer_rewards.models import CustomerReward
from app.rewards.models import Reward
from app.rewards.schemas import RewardCreate, RewardUpdate


async def create_reward(
    db: AsyncSession,
    business_user: BusinessUser,
    data: RewardCreate,
) -> Reward:
    result = await db.execute(
        select(Campaign).where(
            Campaign.id == data.campaign_id,
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
        select(Reward.id).where(
            Reward.campaign_id == campaign.id,
            Reward.deleted_at.is_(None),
        )
    )

    existing_reward_id = result.scalar_one_or_none()

    if existing_reward_id is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Campaign already has a reward",
        )

    reward = Reward(
        campaign_id=campaign.id,
        name=data.name,
        description=data.description,
        reward_type=data.reward_type,
        reward_value=data.reward_value,
        is_active=True,
    )

    db.add(reward)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(reward)

    return reward


async def get_reward_by_id(
    db: AsyncSession,
    reward_id: UUID,
) -> Reward:
    result = await db.execute(
        select(Reward).where(
            Reward.id == reward_id,
            Reward.deleted_at.is_(None),
        )
    )

    reward = result.scalar_one_or_none()

    if reward is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward not found",
        )

    return reward


async def get_business_reward(
    db: AsyncSession,
    business_id: UUID,
    reward_id: UUID,
) -> Reward:
    result = await db.execute(
        select(Reward)
        .join(
            Campaign,
            Reward.campaign_id == Campaign.id,
        )
        .where(
            Reward.id == reward_id,
            Reward.deleted_at.is_(None),
            Campaign.business_id == business_id,
            Campaign.deleted_at.is_(None),
        )
    )

    reward = result.scalar_one_or_none()

    if reward is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward not found",
        )

    return reward


async def get_campaign_rewards(
    db: AsyncSession,
    campaign_id: UUID,
) -> list[Reward]:
    result = await db.execute(
        select(Reward)
        .where(
            Reward.campaign_id == campaign_id,
            Reward.deleted_at.is_(None),
        )
        .order_by(Reward.created_at.asc())
    )

    return list(result.scalars().all())


async def update_reward(
    db: AsyncSession,
    reward: Reward,
    data: RewardUpdate,
) -> Reward:
    update_data = data.model_dump(exclude_unset=True)

    result = await db.execute(
        select(CustomerReward.id)
        .where(
            CustomerReward.reward_id == reward.id,
        )
        .limit(1)
    )

    has_customer_rewards = result.scalar_one_or_none() is not None

    if has_customer_rewards:
        protected_fields = {
            "name",
            "description",
            "reward_type",
            "reward_value",
        }

        if protected_fields.intersection(update_data):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    "Reward details cannot be changed after "
                    "it has been earned by customers"
                ),
            )

    for field, value in update_data.items():
        setattr(reward, field, value)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(reward)

    return reward


async def delete_reward(
    db: AsyncSession,
    reward: Reward,
) -> None:
    reward.deleted_at = datetime.now(timezone.utc)
    reward.is_active = False

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise