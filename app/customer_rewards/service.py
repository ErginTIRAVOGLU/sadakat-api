from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.campaign_memberships.models import CampaignMembership
from app.customer_rewards.models import CustomerReward
from app.loyalty_cards.models import LoyaltyCard
from app.users.models import CustomerProfile


async def get_customer_rewards(
    db: AsyncSession,
    customer: CustomerProfile,
) -> list[CustomerReward]:
    result = await db.execute(
        select(CustomerReward)
        .join(
            LoyaltyCard,
            CustomerReward.loyalty_card_id == LoyaltyCard.id,
        )
        .join(
            CampaignMembership,
            LoyaltyCard.campaign_membership_id == CampaignMembership.id,
        )
        .where(
            CampaignMembership.customer_id == customer.id,
            CustomerReward.deleted_at.is_(None),
        )
        .order_by(
            CustomerReward.earned_at.desc(),
        )
    )

    return list(result.scalars().all())


async def get_customer_reward(
    db: AsyncSession,
    customer: CustomerProfile,
    customer_reward_id: UUID,
) -> CustomerReward:
    result = await db.execute(
        select(CustomerReward)
        .join(
            LoyaltyCard,
            CustomerReward.loyalty_card_id == LoyaltyCard.id,
        )
        .join(
            CampaignMembership,
            LoyaltyCard.campaign_membership_id == CampaignMembership.id,
        )
        .where(
            CustomerReward.id == customer_reward_id,
            CampaignMembership.customer_id == customer.id,
            CustomerReward.deleted_at.is_(None),
        )
    )

    customer_reward = result.scalar_one_or_none()

    if customer_reward is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer reward not found",
        )

    return customer_reward