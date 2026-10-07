from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import require_role
from app.common.enums import UserRole
from app.core.database import get_db
from app.customer_dashboard.schemas import CustomerDashboardResponse
from app.customer_dashboard.service import CustomerDashboardService
from app.users.models import User


router = APIRouter(
    prefix="/customer",
    tags=["Customer Dashboard"],
)


def get_customer_dashboard_service(
    session: AsyncSession = Depends(get_db),
) -> CustomerDashboardService:
    return CustomerDashboardService(session)


@router.get(
    "/dashboard",
    response_model=CustomerDashboardResponse,
)
async def get_customer_dashboard(
    current_user: User = Depends(
        require_role(UserRole.CUSTOMER)
    ),
    service: CustomerDashboardService = Depends(
        get_customer_dashboard_service
    ),
) -> CustomerDashboardResponse:

    customer_profile = current_user.customer_profile

    if customer_profile is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer profile not found",
        )

    return await service.get_dashboard(
        customer_profile_id=customer_profile.id,
        user_id=current_user.id,
    )