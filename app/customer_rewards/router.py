from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.common.enums import UserRole
from app.core.database import get_db
from app.customer_rewards.schemas import CustomerRewardResponse
from app.customer_rewards.service import (
    get_customer_reward,
    get_customer_rewards,
)
from app.users.models import CustomerProfile, User


router = APIRouter(
    prefix="/customer-rewards",
    tags=["Customer Rewards"],
)


async def get_current_customer(
    current_user: User,
    db: AsyncSession,
) -> CustomerProfile:
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account required",
        )

    result = await db.execute(
        select(CustomerProfile).where(
            CustomerProfile.user_id == current_user.id,
        )
    )

    customer = result.scalar_one_or_none()

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer profile not found",
        )

    return customer


@router.get(
    "",
    response_model=list[CustomerRewardResponse],
)
async def list_customer_rewards_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CustomerRewardResponse]:
    customer = await get_current_customer(
        current_user=current_user,
        db=db,
    )

    rewards = await get_customer_rewards(
        db=db,
        customer=customer,
    )

    return [
        CustomerRewardResponse.model_validate(reward)
        for reward in rewards
    ]


@router.get(
    "/{customer_reward_id}",
    response_model=CustomerRewardResponse,
)
async def get_customer_reward_endpoint(
    customer_reward_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CustomerRewardResponse:
    customer = await get_current_customer(
        current_user=current_user,
        db=db,
    )

    reward = await get_customer_reward(
        db=db,
        customer=customer,
        customer_reward_id=customer_reward_id,
    )

    return CustomerRewardResponse.model_validate(reward)