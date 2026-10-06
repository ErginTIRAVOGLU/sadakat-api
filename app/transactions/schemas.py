from typing import Any
from uuid import UUID

from pydantic import BaseModel

from app.common.enums import TransactionType
from app.common.schemas import BaseResponse


class TransactionCreate(BaseModel):
    user_id: UUID
    business_id: UUID | None = None
    type: TransactionType
    reference_id: UUID | None = None
    details: dict[str, Any] | None = None


class TransactionResponse(BaseResponse):
    user_id: UUID
    business_id: UUID | None
    type: TransactionType
    reference_id: UUID | None
    details: dict[str, Any] | None