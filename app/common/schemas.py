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

class SoftDeleteResponse(BaseSchema):
    deleted_at: datetime | None


class BaseResponse(UUIDResponse, TimestampResponse, SoftDeleteResponse):
    pass