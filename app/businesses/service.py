from datetime import datetime, timedelta, timezone
import hashlib
import secrets
from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.businesses.models import Business, BusinessInvitation, BusinessUser
from app.businesses.schemas import (
    BusinessEmployeeInviteCreate,
    BusinessInvitationAcceptRequest,
    BusinessUpdate,
    BusinessUserCreate,
    BusinessUserUpdate,
)
from app.common.enums import BusinessUserRole, UserRole
from app.core.security import create_access_token, hash_password
from app.users.models import User


BUSINESS_INVITATION_EXPIRE_HOURS = 72


async def get_my_business(
    db: AsyncSession,
    business_user: BusinessUser,
) -> Business:
    business = await db.get(
        Business,
        business_user.business_id,
    )

    if business is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business not found",
        )

    return business


async def update_my_business(
    db: AsyncSession,
    business_user: BusinessUser,
    data: BusinessUpdate,
) -> Business:
    business = await get_my_business(
        db=db,
        business_user=business_user,
    )

    update_data = data.model_dump(
        exclude_unset=True,
    )

    for field, value in update_data.items():
        setattr(business, field, value)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(business)

    return business


async def get_business_users(
    db: AsyncSession,
    business_id: UUID,
) -> list[BusinessUser]:
    result = await db.execute(
        select(BusinessUser)
        .where(
            BusinessUser.business_id == business_id,
        )
        .order_by(
            BusinessUser.created_at.asc(),
        )
    )

    return list(result.scalars().all())


async def get_business_user(
    db: AsyncSession,
    business_id: UUID,
    business_user_id: UUID,
) -> BusinessUser:
    result = await db.execute(
        select(BusinessUser).where(
            BusinessUser.id == business_user_id,
            BusinessUser.business_id == business_id,
        )
    )

    business_user = result.scalar_one_or_none()

    if business_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business user not found",
        )

    return business_user


async def create_business_user(
    db: AsyncSession,
    current_business_user: BusinessUser,
    data: BusinessUserCreate,
) -> BusinessUser:
    result = await db.execute(
        select(User).where(
            User.id == data.user_id,
        )
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User is inactive",
        )

    if user.role != UserRole.BUSINESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only business users can be added to a business",
        )

    result = await db.execute(
        select(BusinessUser).where(
            BusinessUser.business_id == current_business_user.business_id,
            BusinessUser.user_id == data.user_id,
        )
    )

    existing_business_user = result.scalar_one_or_none()

    if existing_business_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a member of this business",
        )

    if data.role == BusinessUserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A new business user cannot be assigned the OWNER role",
        )

    business_user = BusinessUser(
        business_id=current_business_user.business_id,
        user_id=data.user_id,
        role=data.role,
    )

    db.add(business_user)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(business_user)

    return business_user


async def update_business_user(
    db: AsyncSession,
    current_business_user: BusinessUser,
    business_user_id: UUID,
    data: BusinessUserUpdate,
) -> BusinessUser:
    business_user = await get_business_user(
        db=db,
        business_id=current_business_user.business_id,
        business_user_id=business_user_id,
    )

    if business_user.id == current_business_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot change your own business role",
        )

    if business_user.role == BusinessUserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OWNER role cannot be changed",
        )

    if data.role == BusinessUserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OWNER role cannot be assigned through employee management",
        )

    business_user.role = data.role

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(business_user)

    return business_user


async def delete_business_user(
    db: AsyncSession,
    current_business_user: BusinessUser,
    business_user_id: UUID,
) -> None:
    business_user = await get_business_user(
        db=db,
        business_id=current_business_user.business_id,
        business_user_id=business_user_id,
    )

    if business_user.id == current_business_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You cannot remove yourself from the business",
        )

    if business_user.role == BusinessUserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OWNER cannot be removed through employee management",
        )

    await db.delete(business_user)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise
    
def hash_invitation_token(token: str) -> str:
    return hashlib.sha256(
        token.encode("utf-8")
    ).hexdigest()
    
async def create_business_invitation(
    db: AsyncSession,
    business_user: BusinessUser,
    data: BusinessEmployeeInviteCreate,
) -> tuple[BusinessInvitation, str]:

    email = str(data.email).lower()

    if data.role == BusinessUserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OWNER role cannot be assigned through employee invitations",
        )

    result = await db.execute(
        select(User).where(
            User.email == email,
        )
    )

    existing_user = result.scalar_one_or_none()

    if existing_user is not None:
        result = await db.execute(
            select(BusinessUser).where(
                BusinessUser.business_id
                == business_user.business_id,
                BusinessUser.user_id
                == existing_user.id,
            )
        )

        existing_membership = result.scalar_one_or_none()

        if existing_membership is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this business",
            )

        if existing_user.role != UserRole.BUSINESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email belongs to a customer account",
            )

    result = await db.execute(
        select(BusinessInvitation).where(
            BusinessInvitation.business_id
            == business_user.business_id,
            BusinessInvitation.email == email,
            BusinessInvitation.accepted_at.is_(None),
        )
    )

    existing_invitation = result.scalar_one_or_none()

    if existing_invitation is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A pending invitation already exists for this email",
        )

    raw_token = secrets.token_urlsafe(32)

    invitation = BusinessInvitation(
        business_id=business_user.business_id,
        email=email,
        role=data.role,
        token_hash=hash_invitation_token(raw_token),
        expires_at=(
            datetime.now(timezone.utc)
            + timedelta(hours=BUSINESS_INVITATION_EXPIRE_HOURS)
        ),
    )

    db.add(invitation)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(invitation)

    return invitation, raw_token

async def accept_business_invitation(
    db: AsyncSession,
    data: BusinessInvitationAcceptRequest,
) -> tuple[User, str]:

    token_hash = hash_invitation_token(data.token)

    result = await db.execute(
        select(BusinessInvitation).where(
            BusinessInvitation.token_hash == token_hash,
        )
    )

    invitation = result.scalar_one_or_none()

    if invitation is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    if invitation.accepted_at is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has already been accepted",
        )

    now = datetime.now(timezone.utc)

    if invitation.expires_at <= now:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invitation has expired",
        )

    result = await db.execute(
        select(User).where(
            User.email == invitation.email,
        )
    )

    user = result.scalar_one_or_none()

    if user is not None:

        if user.role != UserRole.BUSINESS:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This email belongs to a customer account",
            )

        result = await db.execute(
            select(BusinessUser).where(
                BusinessUser.business_id
                == invitation.business_id,
                BusinessUser.user_id
                == user.id,
            )
        )

        existing_membership = result.scalar_one_or_none()

        if existing_membership is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="User is already a member of this business",
            )

    else:
        user = User(
            email=invitation.email,
            password_hash=hash_password(data.password),
            role=UserRole.BUSINESS,
            is_active=True,
            email_verified=False,
        )

        db.add(user)

        await db.flush()

    business_user = BusinessUser(
        business_id=invitation.business_id,
        user_id=user.id,
        role=invitation.role,
    )

    db.add(business_user)

    invitation.accepted_at = now

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(user)

    access_token = create_access_token(user.id)

    return user, access_token


 