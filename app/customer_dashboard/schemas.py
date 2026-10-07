from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DashboardSummaryResponse(BaseModel):
    active_campaigns: int
    active_cards: int
    available_rewards: int
    completed_cards: int


class DashboardRewardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str | None = None
    reward_type: str
    reward_value: str | None = None


class DashboardActiveCardResponse(BaseModel):
    id: UUID
    campaign_id: UUID
    campaign_name: str
    business_id: UUID
    business_name: str

    card_number: int
    required_stamps: int
    current_stamps: int
    remaining_stamps: int
    progress: int

    joined_at: datetime


class DashboardCompletedCardResponse(BaseModel):
    id: UUID
    campaign_id: UUID
    campaign_name: str
    business_id: UUID
    business_name: str

    card_number: int
    required_stamps: int
    completed_stamps: int
    completed_at: datetime

    reward: DashboardRewardResponse | None = None


class DashboardAvailableRewardResponse(BaseModel):
    id: UUID

    campaign_id: UUID
    campaign_name: str

    business_id: UUID
    business_name: str

    reward: DashboardRewardResponse

    earned_at: datetime


class DashboardClaimedRewardResponse(BaseModel):
    id: UUID

    campaign_id: UUID
    campaign_name: str

    business_id: UUID
    business_name: str

    reward: DashboardRewardResponse

    earned_at: datetime
    claimed_at: datetime


class DashboardTransactionResponse(BaseModel):
    id: UUID

    type: str
    title: str
    description: str | None = None

    business_id: UUID | None = None
    business_name: str | None = None

    created_at: datetime


class CustomerDashboardResponse(BaseModel):
    summary: DashboardSummaryResponse

    active_cards: list[DashboardActiveCardResponse]
    available_rewards: list[DashboardAvailableRewardResponse]
    completed_cards: list[DashboardCompletedCardResponse]
    claimed_rewards: list[DashboardClaimedRewardResponse]

    recent_transactions: list[DashboardTransactionResponse]