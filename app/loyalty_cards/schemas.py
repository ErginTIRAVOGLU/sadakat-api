from datetime import datetime
from uuid import UUID

from app.common.enums import LoyaltyCardStatus
from app.common.schemas import BaseResponse


class LoyaltyCardResponse(BaseResponse):
    campaign_membership_id: UUID
    card_number: int
    stamp_count: int
    status: LoyaltyCardStatus
    completed_at: datetime | None