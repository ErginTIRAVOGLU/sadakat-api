import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import RewardClaimStatus
from app.common.models import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base

if TYPE_CHECKING:
    from app.businesses.models import BusinessUser
    from app.customer_rewards.models import CustomerReward


class RewardClaim(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "reward_claims"

    customer_reward_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "customer_rewards.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    business_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "business_users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    status: Mapped[RewardClaimStatus] = mapped_column(
        ENUM(
            RewardClaimStatus,
            name="reward_claim_status",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ],
        ),
        nullable=False,
        default=RewardClaimStatus.USED,
    )

    claimed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    customer_reward: Mapped["CustomerReward"] = relationship(
        "CustomerReward",
        back_populates="reward_claims",
    )

    business_user: Mapped["BusinessUser"] = relationship(
        "BusinessUser",
        back_populates="reward_claims",
    )

    __table_args__ = (
        UniqueConstraint(
            "customer_reward_id",
            name="uq_reward_claims_customer_reward",
        ),
    )