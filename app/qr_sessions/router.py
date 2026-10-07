from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user, require_business_role
from app.businesses.models import BusinessUser
from app.common.enums import BusinessUserRole, UserRole
from app.core.database import get_db
from app.qr_sessions.schemas import QRSessionCreateResponse, QRSessionScanRequest, QRSessionScanResponse
from app.qr_sessions.service import create_qr_session, scan_qr_session
from app.users.models import CustomerProfile, User


router = APIRouter(
    prefix="/qr-sessions",
    tags=["QR Sessions"],
)


@router.post(
    "",
    response_model=QRSessionCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_qr_session_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> QRSessionCreateResponse:

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

    qr_session, token = await create_qr_session(
        db=db,
        customer_id=customer.id,
    )

    return QRSessionCreateResponse(
        id=qr_session.id,
        token=token,
        expires_at=qr_session.expires_at,
        status=qr_session.status,
        created_at=qr_session.created_at,
        updated_at=qr_session.updated_at,
        deleted_at=qr_session.deleted_at,
    )
    
@router.post(
    "/scan",
    response_model=QRSessionScanResponse,
)
async def scan_qr_session_endpoint(
    data: QRSessionScanRequest,
    business_user: BusinessUser = Depends(
        require_business_role(
            BusinessUserRole.OWNER,
            BusinessUserRole.MANAGER,
            BusinessUserRole.STAFF,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> QRSessionScanResponse:
    qr_session, stamp, stamp_count = await scan_qr_session(
        db=db,
        token=data.token,
        campaign_id=data.campaign_id,
        business_user=business_user,
    )

    return QRSessionScanResponse(
        qr_session_id=qr_session.id,
        stamp_id=stamp.id,
        campaign_id=data.campaign_id,
        customer_id=qr_session.customer_id,
        stamp_count=stamp_count,
    )