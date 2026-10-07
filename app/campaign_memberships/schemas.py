from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.common.enums import CampaignMembershipStatus
from app.common.schemas import BaseResponse


class CampaignMembershipCreate(BaseModel):
    campaign_id: UUID


class CampaignMembershipResponse(BaseResponse):
    campaign_id: UUID
    customer_id: UUID
    status: CampaignMembershipStatus
    joined_at: datetime
    completed_at: datetime | None