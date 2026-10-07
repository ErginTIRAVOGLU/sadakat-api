from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.businesses.models import BusinessUser
from app.campaign_memberships.models import CampaignMembership
from app.common.enums import RewardClaimStatus, TransactionType, CustomerRewardStatus

from app.customer_rewards.models import CustomerReward
from app.reward_claims.models import RewardClaim
from app.rewards.models import Reward
from app.transactions.models import Transaction

 


async def create_reward_claims_for_membership(
    db: AsyncSession,
    membership: CampaignMembership,
    stamp_count: int,
) -> list[RewardClaim]:
    result = await db.execute(
        select(Reward).where(
            Reward.campaign_id == membership.campaign_id,
            Reward.is_active.is_(True),
            Reward.deleted_at.is_(None),
            Reward.required_stamps <= stamp_count,
        )
    )

    rewards = result.scalars().all()

    if not rewards:
        return []

    result = await db.execute(
        select(RewardClaim).where(
            RewardClaim.campaign_membership_id == membership.id,
            RewardClaim.status != RewardClaimStatus.CANCELLED,
        )
    )

    existing_reward_ids = {
        claim.reward_id
        for claim in result.scalars().all()
    }

    created_claims: list[RewardClaim] = []

    for reward in rewards:
        if reward.id in existing_reward_ids:
            continue

        now = datetime.now(timezone.utc)

        claim = RewardClaim(
            reward_id=reward.id,
            customer_id=membership.customer_id,
            campaign_membership_id=membership.id,
            status=RewardClaimStatus.AVAILABLE,
            claimed_at=now,
        )

        db.add(claim)
        created_claims.append(claim)

    return created_claims

async def get_customer_reward_claims(
    db: AsyncSession,
    customer_id: UUID,
) -> list[RewardClaim]:
    result = await db.execute(
        select(RewardClaim)
        .options(selectinload(RewardClaim.reward))
        .where(
            RewardClaim.customer_id == customer_id,
        )
        .order_by(RewardClaim.created_at.desc())
    )

    return list(result.scalars().all())


async def get_reward_claim(
    db: AsyncSession,
    claim_id: UUID,
    customer_id: UUID,
) -> RewardClaim:
    result = await db.execute(
        select(RewardClaim)
        .options(selectinload(RewardClaim.reward))
        .where(
            RewardClaim.id == claim_id,
            RewardClaim.customer_id == customer_id,
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
    claim_id: UUID,
    business_user: BusinessUser,
) -> RewardClaim:
    result = await db.execute(
        select(RewardClaim)
        .options(
            selectinload(RewardClaim.reward),
            selectinload(RewardClaim.customer),
        )
        .where(
            RewardClaim.id == claim_id,
        )
    )

    claim = result.scalar_one_or_none()

    if claim is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward claim not found",
        )

    if claim.status != RewardClaimStatus.AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reward claim is not available",
        )

    if (
        claim.reward.campaign.business_id
        != business_user.business_id
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reward does not belong to this business",
        )

    now = datetime.now(timezone.utc)

    if claim.expires_at is not None and claim.expires_at <= now:
        claim.status = RewardClaimStatus.EXPIRED

        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reward claim has expired",
        )

    claim.status = RewardClaimStatus.USED
    claim.used_at = now

    db.add(
        Transaction(
            user_id=claim.customer.user_id,
            business_id=business_user.business_id,
            type=TransactionType.REWARD_USED,
            reference_id=claim.id,
            details={
                "reward_id": str(claim.reward_id),
                "reward_name": claim.reward.name,
            },
        )
    )

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(claim)

    return claim

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
            selectinload(CustomerReward.loyalty_card),
        )
        .where(
            CustomerReward.id == customer_reward_id,
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
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer reward is not available",
        )

    loyalty_card = customer_reward.loyalty_card

    result = await db.execute(
        select(CampaignMembership)
        .options(
            selectinload(CampaignMembership.campaign),
            selectinload(CampaignMembership.customer),
        )
        .where(
            CampaignMembership.id
            == loyalty_card.campaign_membership_id,
        )
    )

    membership = result.scalar_one_or_none()

    if membership is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign membership not found",
        )

    campaign = membership.campaign

    # Campaign must still be valid.
    if not campaign.is_active:
        customer_reward.status = CustomerRewardStatus.EXPIRED

        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign is no longer active",
        )

    if (
        campaign.start_date is not None
        and now < campaign.start_date
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign has not started yet",
        )

    if (
        campaign.end_date is not None
        and now >= campaign.end_date
    ):
        customer_reward.status = CustomerRewardStatus.EXPIRED

        await db.commit()

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Campaign has expired",
        )

    reward_claim = RewardClaim(
        customer_reward_id=customer_reward.id,
        business_user_id=business_user.id,
        status=RewardClaimStatus.USED,
        claimed_at=now,
    )

    db.add(reward_claim)

    customer_reward.status = CustomerRewardStatus.USED

    await db.flush()

    db.add(
        Transaction(
            user_id=membership.customer.user_id,
            business_id=business_user.business_id,
            type=TransactionType.REWARD_CLAIMED,
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