from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.businesses.models import BusinessUser
from app.campaign_memberships.models import CampaignMembership
from app.common.enums import (
    CustomerRewardStatus,
    RewardClaimStatus,
    TransactionType,
)
from app.customer_rewards.models import CustomerReward
from app.loyalty_cards.models import LoyaltyCard
from app.reward_claims.models import RewardClaim
from app.transactions.models import Transaction


async def claim_customer_reward(
    db: AsyncSession,
    customer_reward_id: UUID,
    business_user: BusinessUser,
) -> RewardClaim:
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(CustomerReward)
        .options(
            selectinload(CustomerReward.reward),
            selectinload(CustomerReward.loyalty_card)
            .selectinload(LoyaltyCard.campaign_membership)
            .selectinload(CampaignMembership.campaign),
            selectinload(CustomerReward.loyalty_card)
            .selectinload(LoyaltyCard.campaign_membership)
            .selectinload(CampaignMembership.customer),
        )
        .where(
            CustomerReward.id == customer_reward_id,
            CustomerReward.deleted_at.is_(None),
        )
        .with_for_update()
    )

    customer_reward = result.scalar_one_or_none()

    if customer_reward is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer reward not found",
        )

    if customer_reward.status != CustomerRewardStatus.AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Customer reward is not available",
        )

    loyalty_card = customer_reward.loyalty_card
    membership = loyalty_card.campaign_membership
    campaign = membership.campaign

    if campaign.business_id != business_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer reward not found",
        )

    if not campaign.is_active:
        customer_reward.status = CustomerRewardStatus.EXPIRED

        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign is no longer active",
        )

    if (
        campaign.end_date is not None
        and now >= campaign.end_date
    ):
        customer_reward.status = CustomerRewardStatus.EXPIRED

        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer reward has expired",
        )

    reward_claim = RewardClaim(
        customer_reward_id=customer_reward.id,
        business_user_id=business_user.id,
        status=RewardClaimStatus.USED,
        claimed_at=now,
    )

    customer_reward.status = CustomerRewardStatus.USED

    db.add(reward_claim)

    await db.flush()

    db.add(
        Transaction(
            user_id=membership.customer.user_id,
            business_id=business_user.business_id,
            type=TransactionType.REWARD_USED,
            reference_id=reward_claim.id,
            details={
                "campaign_id": str(campaign.id),
                "campaign_name": campaign.name,
                "customer_reward_id": str(
                    customer_reward.id,
                ),
                "reward_id": str(
                    customer_reward.reward_id,
                ),
                "reward_name": customer_reward.reward.name,
                "loyalty_card_id": str(
                    loyalty_card.id,
                ),
                "card_number": loyalty_card.card_number,
            },
        )
    )

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(reward_claim)

    return reward_claim

async def get_customer_reward_claims(
    db: AsyncSession,
    customer_id: UUID,
) -> list[RewardClaim]:
    result = await db.execute(
        select(RewardClaim)
        .join(
            CustomerReward,
            RewardClaim.customer_reward_id == CustomerReward.id,
        )
        .join(
            LoyaltyCard,
            CustomerReward.loyalty_card_id == LoyaltyCard.id,
        )
        .join(
            CampaignMembership,
            LoyaltyCard.campaign_membership_id
            == CampaignMembership.id,
        )
        .where(
            CampaignMembership.customer_id == customer_id,
        )
        .options(
            selectinload(
                RewardClaim.customer_reward,
            ).selectinload(
                CustomerReward.reward,
            ),
            selectinload(
                RewardClaim.business_user,
            ),
        )
        .order_by(RewardClaim.claimed_at.desc())
    )

    return list(result.scalars().all())


async def get_reward_claim(
    db: AsyncSession,
    claim_id: UUID,
    customer_id: UUID,
) -> RewardClaim:
    result = await db.execute(
        select(RewardClaim)
        .join(
            CustomerReward,
            RewardClaim.customer_reward_id == CustomerReward.id,
        )
        .join(
            LoyaltyCard,
            CustomerReward.loyalty_card_id == LoyaltyCard.id,
        )
        .join(
            CampaignMembership,
            LoyaltyCard.campaign_membership_id
            == CampaignMembership.id,
        )
        .where(
            RewardClaim.id == claim_id,
            CampaignMembership.customer_id == customer_id,
        )
        .options(
            selectinload(
                RewardClaim.customer_reward,
            ).selectinload(
                CustomerReward.reward,
            ),
            selectinload(
                RewardClaim.business_user,
            ),
        )
    )

    claim = result.scalar_one_or_none()

    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward claim not found",
        )

    return claim


async def use_reward_claim(
    db: AsyncSession,
    customer_reward_id: UUID,
    business_user: BusinessUser,
) -> RewardClaim:
    return await claim_customer_reward(
        db=db,
        customer_reward_id=customer_reward_id,
        business_user=business_user,
    )