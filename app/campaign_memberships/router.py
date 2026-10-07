from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.campaign_memberships.schemas import CampaignMembershipResponse
from app.campaign_memberships.service import join_campaign
from app.common.enums import UserRole
from app.core.database import get_db
from app.users.models import CustomerProfile, User


router = APIRouter(
    prefix="/campaigns",
    tags=["Campaign Memberships"],
)


@router.post(
    "/{campaign_id}/join",
    response_model=CampaignMembershipResponse,
    status_code=status.HTTP_201_CREATED,
)
async def join_campaign_endpoint(
    campaign_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CampaignMembershipResponse:

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

    membership = await join_campaign(
        db=db,
        customer=customer,
        campaign_id=campaign_id,
    )

    return CampaignMembershipResponse.model_validate(membership)