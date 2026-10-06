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