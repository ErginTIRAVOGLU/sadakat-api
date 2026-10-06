from uuid import UUID
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


from app.common.enums import BusinessUserRole
from app.common.schemas import BaseResponse


class BusinessCreate(BaseModel):
    name: str = Field(min_length=1, max_length=150)
    slug: str = Field(min_length=1, max_length=180)
    description: str | None = None
    logo_url: str | None = Field(default=None, max_length=500)
    cover_image_url: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    website: str | None = Field(default=None, max_length=500)
    address: str | None = None
    city: str | None = Field(default=None, max_length=100)
    latitude: Decimal | None = None
    longitude: Decimal | None = None


class BusinessUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    logo_url: str | None = Field(default=None, max_length=500)
    cover_image_url: str | None = Field(default=None, max_length=500)
    phone: str | None = Field(default=None, max_length=30)
    email: EmailStr | None = None
    website: str | None = Field(default=None, max_length=500)
    address: str | None = None
    city: str | None = Field(default=None, max_length=100)
    latitude: Decimal | None = None
    longitude: Decimal | None = None
    is_active: bool | None = None


class BusinessResponse(BaseResponse):
    name: str
    slug: str
    description: str | None
    logo_url: str | None
    cover_image_url: str | None
    phone: str | None
    email: EmailStr | None
    website: str | None
    address: str | None
    city: str | None
    latitude: Decimal | None
    longitude: Decimal | None
    is_active: bool
    
    
### BusinessUser

class BusinessUserCreate(BaseModel):
    business_id: UUID
    user_id: UUID
    role: BusinessUserRole = BusinessUserRole.STAFF


class BusinessUserUpdate(BaseModel):
    role: BusinessUserRole


class BusinessUserResponse(BaseResponse):
    business_id: UUID
    user_id: UUID
    role: BusinessUserRole