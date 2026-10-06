from datetime import datetime
from app.businesses.models import TYPE_CHECKING
from uuid import UUID



from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.common.models import UUIDPrimaryKeyMixin, TimestampMixin
from app.core.database import Base


if TYPE_CHECKING:
    from app.businesses.models import Business
    from app.campaign_memberships.models import CampaignMembership
    from app.rewards.models import Reward

class Campaign(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "campaigns"

    business_id: Mapped[UUID] = mapped_column(
        ForeignKey("businesses.id", ondelete="CASCADE"),
        nullable=False,
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

    image_url: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    stamp_target: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    start_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    end_date: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )

    business: Mapped["Business"] = relationship(
        "Business",
        back_populates="campaigns",
    )

    memberships: Mapped[list["CampaignMembership"]] = relationship(
        "CampaignMembership",
        back_populates="campaign",
        cascade="all, delete-orphan",
    )

    rewards: Mapped[list["Reward"]] = relationship(
        "Reward",
        back_populates="campaign",
        cascade="all, delete-orphan",
    )
