
from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import (
    create_access_token,
    hash_password,
    timezone,
    verify_password,
)

from app.users.models import CustomerProfile, User
from app.common.enums import UserRole
from app.common.enums import BusinessUserRole, UserRole
from app.businesses.models import Business, BusinessUser

async def authenticate_user(
    db: AsyncSession,
    email: str,
    password: str,
) -> User:
    result = await db.execute(
        select(User).where(User.email == email)
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not verify_password(password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


async def login(
    db: AsyncSession,
    email: str,
    password: str,
) -> tuple[User, str]:
    user = await authenticate_user(
        db=db,
        email=email,
        password=password,
    )
    
    user.last_login_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(user)

    token = create_access_token(user.id)

    return user, token

async def register_customer(
    db: AsyncSession,
    email: str,
    password: str,
    first_name: str,
    last_name: str,
    phone: str | None,
) -> tuple[User, str]:

    result = await db.execute(
        select(User).where(User.email == email)
    )

    existing_user = result.scalar_one_or_none()

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    user = User(
        email=email,
        password_hash=hash_password(password),
        role=UserRole.CUSTOMER,
        is_active=True,
        email_verified=False,
    )

    customer_profile = CustomerProfile(
        user=user,
        first_name=first_name,
        last_name=last_name,
        phone=phone,
    )

    db.add(user)
    db.add(customer_profile)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(user)

    access_token = create_access_token(user.id)

    return user, access_token

async def register_business(
    db: AsyncSession,
    email: str,
    password: str,
    business_name: str,
    slug: str,
    description: str | None,
    phone: str | None,
    website: str | None,
    address: str | None,
    city: str | None,
) -> tuple[User, str]:
    result = await db.execute(
        select(User).where(User.email == email)
    )
    existing_user = result.scalar_one_or_none()

    if existing_user is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A user with this email already exists",
        )

    result = await db.execute(
        select(Business).where(Business.slug == slug)
    )
    existing_business = result.scalar_one_or_none()

    if existing_business is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="A business with this slug already exists",
        )

    user = User(
        email=email,
        password_hash=hash_password(password),
        role=UserRole.BUSINESS,
        is_active=True,
        email_verified=False,
    )

    business = Business(
        name=business_name,
        slug=slug,
        description=description,
        phone=phone,
        email=email,
        website=website,
        address=address,
        city=city,
        is_active=True,
    )

    business_user = BusinessUser(
        user=user,
        business=business,
        role=BusinessUserRole.OWNER,
    )

    db.add(user)
    db.add(business)
    db.add(business_user)

    try:
        await db.commit()
    except Exception:
        await db.rollback()
        raise

    await db.refresh(user)

    access_token = create_access_token(user.id)

    return user, access_token

