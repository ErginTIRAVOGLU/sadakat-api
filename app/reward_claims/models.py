from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import RewardClaimStatus
from app.common.models import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base

if TYPE_CHECKING:
    from app.campaign_memberships.models import CampaignMembership
    from app.rewards.models import Reward
    from app.users.models import CustomerProfile


class RewardClaim(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "reward_claims"

    reward_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "rewards.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "customer_profiles.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    campaign_membership_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "campaign_memberships.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    status: Mapped[RewardClaimStatus] = mapped_column(
        SAEnum(
            RewardClaimStatus,
            name="reward_claim_status",
        ),
        nullable=False,
        default=RewardClaimStatus.AVAILABLE,
    )

    claimed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    reward: Mapped["Reward"] = relationship(
        "Reward",
        back_populates="reward_claims",
    )

    customer: Mapped["CustomerProfile"] = relationship(
        "CustomerProfile",
        back_populates="reward_claims",
    )

    campaign_membership: Mapped["CampaignMembership"] = relationship(
        "CampaignMembership",
        back_populates="reward_claims",
    )