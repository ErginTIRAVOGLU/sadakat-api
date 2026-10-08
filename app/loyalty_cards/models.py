from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import ENUM, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import LoyaltyCardStatus
from app.common.models import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


if TYPE_CHECKING:
    from app.campaign_memberships.models import CampaignMembership
    from app.customer_rewards.models import CustomerReward
    from app.stamps.models import Stamp


class LoyaltyCard(
    UUIDPrimaryKeyMixin,
    TimestampMixin,
    Base,
):
    __tablename__ = "loyalty_cards"

    __table_args__ = (
        UniqueConstraint(
            "campaign_membership_id",
            "card_number",
            name="uq_loyalty_cards_membership_card_number",
        ),
    )

    campaign_membership_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey(
            "campaign_memberships.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    card_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    stamp_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )

    status: Mapped[LoyaltyCardStatus] = mapped_column(
        ENUM(
            LoyaltyCardStatus,
            name="loyalty_card_status",
            values_callable=lambda enum_class: [
                item.value for item in enum_class
            ], 
        ),
        nullable=False,
        default=LoyaltyCardStatus.ACTIVE,
        server_default=LoyaltyCardStatus.ACTIVE.value,
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    campaign_membership: Mapped["CampaignMembership"] = relationship(
        "CampaignMembership",
        back_populates="loyalty_cards",
    )

    stamps: Mapped[list["Stamp"]] = relationship(
        "Stamp",
        back_populates="loyalty_card",
        cascade="all, delete-orphan",
    )

    customer_rewards: Mapped[list["CustomerReward"]] = relationship(
        "CustomerReward",
        back_populates="loyalty_card",
    )