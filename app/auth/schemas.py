from pydantic import BaseModel, EmailStr, Field

from app.common.schemas import BaseSchema
from app.users.schemas import UserResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class AuthResponse(BaseSchema):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"


class CurrentUserResponse(BaseSchema):
    user: UserResponse
    

class CustomerRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: str | None = Field(default=None, max_length=30)

class BusinessRegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)

    business_name: str = Field(min_length=1, max_length=150)
    slug: str = Field(min_length=1, max_length=180)

    description: str | None = None
    phone: str | None = Field(default=None, max_length=30)
    website: str | None = Field(default=None, max_length=500)
    address: str | None = None
    city: str | None = Field(default=None, max_length=100)