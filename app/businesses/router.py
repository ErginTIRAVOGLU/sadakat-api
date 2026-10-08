from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import (
    get_current_business_user,
    require_business_role,
)
from app.auth.schemas import AuthResponse
from app.businesses.models import BusinessUser
from app.businesses.schemas import (
    BusinessInvitationCreateResponse,
    BusinessResponse,
    BusinessUpdate,
    BusinessUserCreate,
    BusinessUserResponse,
    BusinessUserUpdate,
)
from app.businesses.service import (
    BusinessEmployeeInviteCreate,
    BusinessInvitationAcceptRequest,
    accept_business_invitation,
    create_business_invitation,
    create_business_user,
    delete_business_user,
    get_business_users,
    get_my_business,
    update_business_user,
    update_my_business,
)
from app.common.enums import BusinessUserRole
from app.core.database import get_db


router = APIRouter(
    prefix="/business",
    tags=["Business"],
)


@router.get(
    "/me",
    response_model=BusinessResponse,
)
async def get_business_profile(
    business_user: BusinessUser = Depends(
        get_current_business_user,
    ),
    db: AsyncSession = Depends(get_db),
):
    return await get_my_business(
        db=db,
        business_user=business_user,
    )


@router.put(
    "/me",
    response_model=BusinessResponse,
)
async def update_business_profile(
    data: BusinessUpdate,
    business_user: BusinessUser = Depends(
        require_business_role(
            BusinessUserRole.OWNER,
            BusinessUserRole.MANAGER,
        )
    ),
    db: AsyncSession = Depends(get_db),
):
    return await update_my_business(
        db=db,
        business_user=business_user,
        data=data,
    )


@router.get(
    "/users",
    response_model=list[BusinessUserResponse],
)
async def list_business_users(
    business_user: BusinessUser = Depends(
        get_current_business_user,
    ),
    db: AsyncSession = Depends(get_db),
) -> list[BusinessUserResponse]:
    users = await get_business_users(
        db=db,
        business_id=business_user.business_id,
    )

    return [
        BusinessUserResponse.model_validate(user)
        for user in users
    ]


@router.post(
    "/users",
    response_model=BusinessUserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_business_user_endpoint(
    data: BusinessUserCreate,
    business_user: BusinessUser = Depends(
        require_business_role(
            BusinessUserRole.OWNER,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> BusinessUserResponse:
    business_user = await create_business_user(
        db=db,
        current_business_user=business_user,
        data=data,
    )

    return BusinessUserResponse.model_validate(
        business_user,
    )


@router.put(
    "/users/{business_user_id}",
    response_model=BusinessUserResponse,
)
async def update_business_user_endpoint(
    business_user_id: UUID,
    data: BusinessUserUpdate,
    business_user: BusinessUser = Depends(
        require_business_role(
            BusinessUserRole.OWNER,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> BusinessUserResponse:
    business_user = await update_business_user(
        db=db,
        current_business_user=business_user,
        business_user_id=business_user_id,
        data=data,
    )

    return BusinessUserResponse.model_validate(
        business_user,
    )


@router.delete(
    "/users/{business_user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_business_user_endpoint(
    business_user_id: UUID,
    business_user: BusinessUser = Depends(
        require_business_role(
            BusinessUserRole.OWNER,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> None:
    await delete_business_user(
        db=db,
        current_business_user=business_user,
        business_user_id=business_user_id,
    )
    
@router.post(
    "/employees/invite",
    response_model=BusinessInvitationCreateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def invite_business_employee(
    data: BusinessEmployeeInviteCreate,
    business_user: BusinessUser = Depends(
        require_business_role(
            BusinessUserRole.OWNER,
        )
    ),
    db: AsyncSession = Depends(get_db),
) -> BusinessInvitationCreateResponse:

    invitation, token = await create_business_invitation(
        db=db,
        business_user=business_user,
        data=data,
    )

    return BusinessInvitationCreateResponse(
        id=invitation.id,
        created_at=invitation.created_at,
        updated_at=invitation.updated_at,
        deleted_at=invitation.deleted_at,
        business_id=invitation.business_id,
        email=invitation.email,
        role=invitation.role,
        expires_at=invitation.expires_at,
        accepted_at=invitation.accepted_at,
        token=token,
    )
    
@router.post(
    "/employees/invitations/accept",
    response_model=AuthResponse,
)
async def accept_business_employee_invitation(
    data: BusinessInvitationAcceptRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:

    user, access_token = await accept_business_invitation(
        db=db,
        data=data,
    )

    return AuthResponse(
        user=user,
        access_token=access_token,
    )
