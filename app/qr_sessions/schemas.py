from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.common.enums import QRSessionStatus
from app.common.schemas import BaseResponse


class QRSessionCreate(BaseModel):
    customer_id: UUID
    expires_at: datetime


class QRSessionResponse(BaseResponse):
    customer_id: UUID
    business_id: UUID | None
    expires_at: datetime
    used_at: datetime | None
    status: QRSessionStatus


class QRSessionCreateResponse(QRSessionResponse):
    token: str