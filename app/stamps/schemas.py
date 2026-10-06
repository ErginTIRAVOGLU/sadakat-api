from uuid import UUID

from pydantic import BaseModel

from app.common.schemas import BaseResponse


class StampCreate(BaseModel):
    campaign_membership_id: UUID
    qr_session_id: UUID
    business_user_id: UUID


class StampResponse(BaseResponse):
    campaign_membership_id: UUID
    qr_session_id: UUID
    business_user_id: UUID