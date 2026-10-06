from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.common.enums import UserRole
from app.common.schemas import BaseResponse


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class UserUpdate(BaseModel):
    email: EmailStr | None = None
    is_active: bool | None = None


class UserResponse(BaseResponse):
    email: EmailStr
    role: UserRole
    is_active: bool
    email_verified: bool
    last_login_at: datetime | None = None


class CustomerProfileCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    avatar_url: str | None = Field(default=None, max_length=500)


class CustomerProfileUpdate(BaseModel):
    first_name: str | None = Field(default=None, min_length=1, max_length=100)
    last_name: str | None = Field(default=None, min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=30)
    avatar_url: str | None = Field(default=None, max_length=500)


class CustomerProfileResponse(BaseResponse):
    user_id: UUID
    first_name: str
    last_name: str
    phone: str | None
    avatar_url: str | None