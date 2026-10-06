from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class BaseSchema(BaseModel):
    model_config = ConfigDict(
        from_attributes=True,
    )


class UUIDResponse(BaseSchema):
    id: UUID


class TimestampResponse(BaseSchema):
    created_at: datetime
    updated_at: datetime
    deleted_at: datetime


class BaseResponse(UUIDResponse, TimestampResponse):
    pass