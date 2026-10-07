from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import (
    get_current_user,
    require_business_role,
)
from app.businesses.models import BusinessUser
from app.campaigns.schemas import CampaignCreate, CampaignResponse, CampaignUpdate
from app.campaigns.service import (
    create_campaign,
    delete_campaign,
    get_active_campaigns,
    get_business_campaigns,
    get_campaign_by_id,
    update_campaign,
)
from app.common.enums import BusinessUserRole, UserRole
from app.core.database import get_db
from app.users.models import User


router = APIRouter(
    prefix="/campaigns",
    tags=["Campaigns"],
)


@router.post(
    "",
    response_model=CampaignResponse,
    status_code=201,
)
async def create_campaign_endpoint(
    data: CampaignCreate,
    business_user: BusinessUser = Depends(
        require_business_role(
            BusinessUserRole.OWNER,
            BusinessUserRole.MANAGER,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    campaign = await create_campaign(
        db=db,
        business_user=business_user,
        data=data,
    )

    return CampaignResponse.model_validate(campaign)

@router.get(
    "",
    response_model=list[CampaignResponse],
)
async def list_campaigns_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[CampaignResponse]:
    if current_user.role == UserRole.BUSINESS:
        result = await db.execute(
            select(BusinessUser).where(
                BusinessUser.user_id == current_user.id,
            )
        )

        business_user = result.scalar_one_or_none()

        if business_user is None:
            raise HTTPException(
                status_code=403,
                detail="Business membership not found",
            )

        campaigns = await get_business_campaigns(
            db=db,
            business_id=business_user.business_id,
        )

    elif current_user.role == UserRole.CUSTOMER:
        campaigns = await get_active_campaigns(db=db)

    elif current_user.role == UserRole.ADMIN:
        campaigns = await get_active_campaigns(db=db)

    else:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions",
        )

    return [
        CampaignResponse.model_validate(campaign)
        for campaign in campaigns
    ]
    
@router.get(
    "/{campaign_id}",
    response_model=CampaignResponse,
)
async def get_campaign_endpoint(
    campaign_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    campaign = await get_campaign_by_id(
        db=db,
        campaign_id=campaign_id,
    )

    if current_user.role == UserRole.CUSTOMER:
        if not campaign.is_active:
            raise HTTPException(
                status_code=404,
                detail="Campaign not found",
            )

    elif current_user.role == UserRole.BUSINESS:
        result = await db.execute(
            select(BusinessUser).where(
                BusinessUser.user_id == current_user.id,
            )
        )

        business_user = result.scalar_one_or_none()

        if business_user is None:
            raise HTTPException(
                status_code=403,
                detail="Business membership not found",
            )

        if campaign.business_id != business_user.business_id:
            raise HTTPException(
                status_code=404,
                detail="Campaign not found",
            )

    elif current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=403,
            detail="Insufficient permissions",
        )

    return CampaignResponse.model_validate(campaign)

@router.put(
    "/{campaign_id}",
    response_model=CampaignResponse,
)
async def update_campaign_endpoint(
    campaign_id: UUID,
    data: CampaignUpdate,
    business_user: BusinessUser = Depends(
        require_business_role(
            BusinessUserRole.OWNER,
            BusinessUserRole.MANAGER,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> CampaignResponse:
    campaign = await get_campaign_by_id(
        db=db,
        campaign_id=campaign_id,
    )

    if campaign.business_id != business_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    campaign = await update_campaign(
        db=db,
        campaign=campaign,
        data=data,
    )

    return CampaignResponse.model_validate(campaign)

@router.delete(
    "/{campaign_id}",
    status_code=204,
)
async def delete_campaign_endpoint(
    campaign_id: UUID,
    business_user: BusinessUser = Depends(
        require_business_role(
            BusinessUserRole.OWNER,
            BusinessUserRole.MANAGER,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> None:
    campaign = await get_campaign_by_id(
        db=db,
        campaign_id=campaign_id,
    )

    if campaign.business_id != business_user.business_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Campaign not found",
        )

    await delete_campaign(
        db=db,
        campaign=campaign,
    )