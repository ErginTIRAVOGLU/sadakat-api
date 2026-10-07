from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.common.enums import RewardClaimStatus
from app.common.schemas import BaseResponse


class RewardClaimCreate(BaseModel):
    reward_id: UUID
    customer_id: UUID
    campaign_membership_id: UUID

class RewardClaimResponse(BaseResponse):
    reward_id: UUID
    customer_id: UUID
    campaign_membership_id: UUID
    status: RewardClaimStatus
    claimed_at: datetime
    used_at: datetime | None
    expires_at: datetime | None


class RewardClaimDetailResponse(RewardClaimResponse):
    reward_name: str
    reward_description: str | None
    reward_type: str
    reward_value: str | None