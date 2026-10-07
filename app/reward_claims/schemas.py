from datetime import datetime
from uuid import UUID

from app.common.enums import RewardClaimStatus
from app.common.schemas import BaseResponse


class RewardClaimResponse(BaseResponse):
    customer_reward_id: UUID
    business_user_id: UUID
    status: RewardClaimStatus
    claimed_at: datetime


class RewardClaimDetailResponse(RewardClaimResponse):
    reward_name: str
    reward_description: str | None
    reward_type: str
    reward_value: str | None