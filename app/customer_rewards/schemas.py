from datetime import datetime
from uuid import UUID

from app.common.enums import CustomerRewardStatus
from app.common.schemas import BaseResponse


class CustomerRewardResponse(BaseResponse):
    reward_id: UUID
    loyalty_card_id: UUID
    status: CustomerRewardStatus
    earned_at: datetime