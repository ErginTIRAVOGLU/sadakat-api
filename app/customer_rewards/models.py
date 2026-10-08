from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import CustomerRewardStatus
from app.common.models import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base

if TYPE_CHECKING:
    from app.loyalty_cards.models import LoyaltyCard
    from app.rewards.models import Reward
    from app.reward_claims.models import RewardClaim


class CustomerReward(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "customer_rewards"

    __table_args__ = (
        UniqueConstraint(
            "loyalty_card_id",
            name="uq_customer_rewards_loyalty_card",
        ),
    )

    reward_id: Mapped[UUID] = mapped_column(
        ForeignKey("rewards.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    loyalty_card_id: Mapped[UUID] = mapped_column(
        ForeignKey("loyalty_cards.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )

    status: Mapped[CustomerRewardStatus] = mapped_column(
        ENUM(
            CustomerRewardStatus,
            name="customer_reward_status",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ], 
        ),
        nullable=False,
        default=CustomerRewardStatus.AVAILABLE,
    )

    earned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    reward: Mapped["Reward"] = relationship(
        "Reward",
        back_populates="customer_rewards",
    )

    loyalty_card: Mapped["LoyaltyCard"] = relationship(
        "LoyaltyCard",
        back_populates="customer_rewards",
    )

    reward_claims: Mapped[list["RewardClaim"]] = relationship(
        "RewardClaim",
        back_populates="customer_reward",
    )