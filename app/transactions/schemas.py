from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.common.enums import TransactionType
from app.common.schemas import BaseResponse


class TransactionResponse(BaseResponse):
    user_id: UUID
    business_id: UUID | None
    type: TransactionType
    reference_id: UUID | None
    details: dict | None


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int