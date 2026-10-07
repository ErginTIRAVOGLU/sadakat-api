from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_business_role
from app.businesses.models import BusinessUser
from app.common.enums import BusinessUserRole, UserRole
from app.core.database import get_db
from app.campaigns.models import Campaign
from app.rewards.schemas import (
    RewardCreate,
    RewardResponse,
    RewardUpdate,
)
from app.rewards.service import (
    create_reward,
    delete_reward,
    get_campaign_rewards,
    get_reward_by_id,
    update_reward,
)
from app.users.models import User


router = APIRouter(
    prefix="/rewards",
    tags=["Rewards"],
)

@router.post(
    "",
    response_model=RewardResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_reward_endpoint(
    data: RewardCreate,
    business_user: BusinessUser = Depends(
        require_business_role(
            BusinessUserRole.OWNER,
            BusinessUserRole.MANAGER,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> RewardResponse:
    reward = await create_reward(
        db=db,
        business_user=business_user,
        data=data,
    )

    return RewardResponse.model_validate(reward)

@router.get(
    "/campaign/{campaign_id}",
    response_model=list[RewardResponse],
)
async def list_campaign_rewards_endpoint(
    campaign_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[RewardResponse]:
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

    if current_user.role == UserRole.CUSTOMER:
        if not campaign.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found",
            )

    elif current_user.role == UserRole.BUSINESS:
        result = await db.execute(
            select(BusinessUser).where(
                BusinessUser.user_id == current_user.id,
                BusinessUser.business_id == campaign.business_id,
            )
        )

        business_user = result.scalar_one_or_none()

        if business_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Campaign not found",
            )

    elif current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    rewards = await get_campaign_rewards(
        db=db,
        campaign_id=campaign_id,
    )

    return [
        RewardResponse.model_validate(reward)
        for reward in rewards
    ]
    
@router.get(
    "/{reward_id}",
    response_model=RewardResponse,
)
async def get_reward_endpoint(
    reward_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RewardResponse:
    reward = await get_reward_by_id(
        db=db,
        reward_id=reward_id,
    )

    result = await db.execute(
        select(Campaign).where(
            Campaign.id == reward.campaign_id,
            Campaign.deleted_at.is_(None),
        )
    )

    campaign = result.scalar_one_or_none()

    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    if current_user.role == UserRole.CUSTOMER:
        if not campaign.is_active or not reward.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reward not found",
            )

    elif current_user.role == UserRole.BUSINESS:
        result = await db.execute(
            select(BusinessUser).where(
                BusinessUser.user_id == current_user.id,
                BusinessUser.business_id == campaign.business_id,
            )
        )

        business_user = result.scalar_one_or_none()

        if business_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Reward not found",
            )

    elif current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return RewardResponse.model_validate(reward)

@router.put(
    "/{reward_id}",
    response_model=RewardResponse,
)
async def update_reward_endpoint(
    reward_id: UUID,
    data: RewardUpdate,
    business_user: BusinessUser = Depends(
        require_business_role(
            BusinessUserRole.OWNER,
            BusinessUserRole.MANAGER,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> RewardResponse:
    reward = await get_reward_by_id(
        db=db,
        reward_id=reward_id,
    )

    result = await db.execute(
        select(Campaign).where(
            Campaign.id == reward.campaign_id,
            Campaign.deleted_at.is_(None),
        )
    )

    campaign = result.scalar_one_or_none()

    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    if campaign.business_id != business_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward not found",
        )

    reward = await update_reward(
        db=db,
        reward=reward,
        data=data,
    )

    return RewardResponse.model_validate(reward)

@router.delete(
    "/{reward_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_reward_endpoint(
    reward_id: UUID,
    business_user: BusinessUser = Depends(
        require_business_role(
            BusinessUserRole.OWNER,
            BusinessUserRole.MANAGER,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> None:
    reward = await get_reward_by_id(
        db=db,
        reward_id=reward_id,
    )

    result = await db.execute(
        select(Campaign).where(
            Campaign.id == reward.campaign_id,
            Campaign.deleted_at.is_(None),
        )
    )

    campaign = result.scalar_one_or_none()

    if campaign is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    if campaign.business_id != business_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Reward not found",
        )

    await delete_reward(
        db=db,
        reward=reward,
    )