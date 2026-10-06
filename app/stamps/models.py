from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.models import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base

if TYPE_CHECKING:
    from app.businesses.models import BusinessUser
    from app.campaign_memberships.models import CampaignMembership
    from app.qr_sessions.models import QRSession


class Stamp(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "stamps"

    campaign_membership_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "campaign_memberships.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    qr_session_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "qr_sessions.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    business_user_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "business_users.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    membership: Mapped["CampaignMembership"] = relationship(
        "CampaignMembership",
        back_populates="stamps",
    )

    qr_session: Mapped["QRSession"] = relationship(
        "QRSession",
        back_populates="stamp",
    )

    business_user: Mapped["BusinessUser"] = relationship(
        "BusinessUser",
        back_populates="stamps",
    )