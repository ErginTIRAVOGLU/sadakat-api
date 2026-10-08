from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Boolean, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import RewardType
from app.common.models import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base

if TYPE_CHECKING:
    from app.campaigns.models import Campaign
    from app.customer_rewards.models import CustomerReward


class Reward(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "rewards"

    campaign_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "campaigns.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    reward_type: Mapped[RewardType] = mapped_column(
        ENUM(
            RewardType,
            name="reward_type", 
        ),
        nullable=False,
        
    )

    reward_value: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )

    campaign: Mapped["Campaign"] = relationship(
        "Campaign",
        back_populates="reward",
    )

    customer_rewards: Mapped[list["CustomerReward"]] = relationship(
        "CustomerReward",
        back_populates="reward",
    )