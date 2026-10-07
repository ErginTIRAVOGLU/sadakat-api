from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.common.enums import QRSessionStatus
from app.common.schemas import BaseResponse


class QRSessionCreateResponse(BaseResponse):
    token: str
    expires_at: datetime
    status: QRSessionStatus


class QRSessionResponse(BaseResponse):
    customer_id: UUID
    business_id: UUID | None
    expires_at: datetime
    used_at: datetime | None
    status: QRSessionStatus


class QRSessionScanRequest(BaseModel):
    token: str = Field(min_length=1)
    campaign_id: UUID


class QRSessionScanResponse(BaseModel):
    qr_session_id: UUID
    stamp_id: UUID
    campaign_id: UUID
    customer_id: UUID
    stamp_count: int