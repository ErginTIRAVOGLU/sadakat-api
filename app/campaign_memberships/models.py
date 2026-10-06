from datetime import datetime
from uuid import UUID


from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import Enum as SAEnum

from app.common.enums import CampaignMembershipStatus
from app.common.models import UUIDPrimaryKeyMixin, TimestampMixin
from app.core.database import Base


class CampaignMembership(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "campaign_memberships"

    campaign_id: Mapped[UUID] = mapped_column(
        ForeignKey("campaigns.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey("customer_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    status: Mapped[CampaignMembershipStatus] = mapped_column(
        SAEnum(
            CampaignMembershipStatus,
            name="campaign_membership_status",
        ),
        nullable=False,
        default=CampaignMembershipStatus.ACTIVE,
    )

    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    campaign = relationship(
        "Campaign",
        back_populates="memberships",
    )

    customer = relationship(
        "CustomerProfile",
        back_populates="campaign_memberships",
    )

    stamps = relationship(
        "Stamp",
        back_populates="membership",
        cascade="all, delete-orphan",
    )
    
    reward_claims = relationship(
        "RewardClaim",
        back_populates="campaign_membership",
    )

    __table_args__ = (
        UniqueConstraint(
            "campaign_id",
            "customer_id",
            name="uq_campaign_membership_campaign_customer",
        ),
    )