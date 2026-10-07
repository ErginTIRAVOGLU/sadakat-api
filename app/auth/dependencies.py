from uuid import UUID
from collections.abc import Callable



from fastapi import Depends, HTTPException, status
# from fastapi.security import OAuth2PasswordBearer
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.businesses.models import BusinessUser
from app.core.database import get_db
from app.core.security import decode_access_token
from app.users.models import User
from app.common.enums import BusinessUserRole, UserRole

# oauth2_scheme = OAuth2PasswordBearer(
#     tokenUrl="/api/v1/auth/login",
# )
 

security = HTTPBearer()

async def get_current_user(
#    token: str = Depends(oauth2_scheme),
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials
    try:
        user_id: UUID = decode_access_token(token)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(
        select(User).where(
            User.id == user_id,
            User.is_active.is_(True),
        )
    )

    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user

def require_role(*allowed_roles: UserRole):
    async def dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )

        return current_user

    return dependency

async def get_current_business_user(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> BusinessUser:
    if current_user.role != UserRole.BUSINESS:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business account required",
        )

    result = await db.execute(
        select(BusinessUser).where(
            BusinessUser.user_id == current_user.id,
        )
    )

    business_user = result.scalar_one_or_none()

    if business_user is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Business membership not found",
        )

    return business_user


def require_business_role(
    *allowed_roles: BusinessUserRole,
) -> Callable:
    async def dependency(
        business_user: BusinessUser = Depends(
            get_current_business_user,
        ),
    ) -> BusinessUser:
        if business_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient business permissions",
            )

        return business_user

    return dependency