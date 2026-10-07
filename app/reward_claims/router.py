from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import (
    get_current_user,
    require_business_role,
)
from app.businesses.models import BusinessUser
from app.common.enums import BusinessUserRole, UserRole
from app.core.database import get_db
from app.reward_claims.schemas import (
    RewardClaimDetailResponse,
    RewardClaimResponse,
)
from app.reward_claims.service import (
    get_customer_reward_claims,
    get_reward_claim,
    use_reward_claim,
)
from app.users.models import CustomerProfile, User


router = APIRouter(
    prefix="/reward-claims",
    tags=["Reward Claims"],
)


@router.get(
    "",
    response_model=list[RewardClaimDetailResponse],
)
async def list_my_reward_claims(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RewardClaimDetailResponse]:
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found",
        )

    claims = await get_customer_reward_claims(
        db=db,
        customer_id=customer.id,
    )

    return [
        RewardClaimDetailResponse(
            **RewardClaimResponse.model_validate(claim).model_dump(),
            reward_name=claim.customer_reward.reward.name,
            reward_description=claim.customer_reward.reward.description,
            reward_type=claim.customer_reward.reward.reward_type.value,
            reward_value=claim.customer_reward.reward.reward_value,
        )
        for claim in claims
    ]


@router.get(
    "/{claim_id}",
    response_model=RewardClaimDetailResponse,
)
async def get_my_reward_claim(
    claim_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RewardClaimDetailResponse:
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
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Customer profile not found",
        )

    claim = await get_reward_claim(
        db=db,
        claim_id=claim_id,
        customer_id=customer.id,
    )

    return RewardClaimDetailResponse(
        **RewardClaimResponse.model_validate(claim).model_dump(),
        reward_name=claim.customer_reward.reward.name,
        reward_description=claim.customer_reward.reward.description,
        reward_type=claim.customer_reward.reward.reward_type.value,
        reward_value=claim.customer_reward.reward.reward_value,
    )


@router.post(
    "/{claim_id}/use",
    response_model=RewardClaimResponse,
)
async def use_reward_claim_endpoint(
    claim_id: UUID,
    business_user: BusinessUser = Depends(
        require_business_role(
            BusinessUserRole.OWNER,
            BusinessUserRole.MANAGER,
            BusinessUserRole.STAFF,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> RewardClaimResponse:
    claim = await use_reward_claim(
        db=db,
        claim_id=claim_id,
        business_user=business_user,
    )

    return RewardClaimResponse.model_validate(claim)