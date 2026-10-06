from uuid import UUID

from pydantic import BaseModel, Field

from app.common.enums import RewardType
from app.common.schemas import BaseResponse


class RewardCreate(BaseModel):
    campaign_id: UUID
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    required_stamps: int = Field(gt=0)
    reward_type: RewardType
    reward_value: str | None = Field(default=None, max_length=255)


class RewardUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    required_stamps: int | None = Field(default=None, gt=0)
    reward_type: RewardType | None = None
    reward_value: str | None = Field(default=None, max_length=255)
    is_active: bool | None = None


class RewardResponse(BaseResponse):
    campaign_id: UUID
    name: str
    description: str | None
    required_stamps: int
    reward_type: RewardType
    reward_value: str | None
    is_active: bool