from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.schemas import AuthResponse, CurrentUserResponse, LoginRequest
from app.auth.service import login
from app.core.database import get_db
from app.users.models import User


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/login",
    response_model=AuthResponse,
)
async def login_endpoint(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AuthResponse:
    user, access_token = await login(
        db=db,
        email=request.email,
        password=request.password,
    )

    return AuthResponse(
        user=user,
        access_token=access_token,
    )


@router.get(
    "/me",
    response_model=CurrentUserResponse,
)
async def me(
    current_user: User = Depends(get_current_user),
) -> CurrentUserResponse:
    return CurrentUserResponse(
        user=current_user,
    )