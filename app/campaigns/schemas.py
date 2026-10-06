from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.common.schemas import BaseResponse


class CampaignCreate(BaseModel):
    business_id: UUID
    name: str = Field(min_length=1, max_length=150)
    description: str | None = None
    image_url: str | None = None
    stamp_target: int = Field(gt=0)
    start_date: datetime | None = None
    end_date: datetime | None = None


class CampaignUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=150)
    description: str | None = None
    image_url: str | None = None
    stamp_target: int | None = Field(default=None, gt=0)
    start_date: datetime | None = None
    end_date: datetime | None = None
    is_active: bool | None = None


class CampaignResponse(BaseResponse):
    business_id: UUID
    name: str
    description: str | None
    image_url: str | None
    stamp_target: int
    start_date: datetime | None
    end_date: datetime | None
    is_active: bool