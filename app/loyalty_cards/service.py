from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.campaign_memberships.models import CampaignMembership
from app.loyalty_cards.models import LoyaltyCard
from app.users.models import CustomerProfile


async def get_customer_loyalty_cards(
    db: AsyncSession,
    customer: CustomerProfile,
) -> list[LoyaltyCard]:
    result = await db.execute(
        select(LoyaltyCard)
        .join(
            CampaignMembership,
            LoyaltyCard.campaign_membership_id == CampaignMembership.id,
        )
        .where(
            CampaignMembership.customer_id == customer.id,
            LoyaltyCard.deleted_at.is_(None),
        )
        .order_by(
            LoyaltyCard.created_at.desc(),
        )
    )

    return list(result.scalars().all())


async def get_customer_loyalty_card(
    db: AsyncSession,
    customer: CustomerProfile,
    card_id: UUID,
) -> LoyaltyCard:
    result = await db.execute(
        select(LoyaltyCard)
        .join(
            CampaignMembership,
            LoyaltyCard.campaign_membership_id == CampaignMembership.id,
        )
        .where(
            LoyaltyCard.id == card_id,
            CampaignMembership.customer_id == customer.id,
            LoyaltyCard.deleted_at.is_(None),
        )
    )

    card = result.scalar_one_or_none()

    if card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Loyalty card not found",
        )

    return card