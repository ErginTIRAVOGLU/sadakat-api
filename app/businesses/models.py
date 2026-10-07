import uuid
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import BusinessUserRole
from app.common.models import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


if TYPE_CHECKING:
    from app.transactions.models import Transaction
    from app.users.models import User
    from app.qr_sessions.models import QRSession
    from app.stamps.models import Stamp
    from app.campaigns.models import Campaign
    from app.reward_claims.models import RewardClaim


class Business(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "businesses"

    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
    )

    slug: Mapped[str] = mapped_column(
        String(180),
        unique=True,
        nullable=False,
        index=True,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    logo_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    cover_image_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    email: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    website: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    address: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    city: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    latitude: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
    )

    longitude: Mapped[Decimal | None] = mapped_column(
        Numeric(10, 7),
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )

    business_users: Mapped[list["BusinessUser"]] = relationship(
        "BusinessUser",
        back_populates="business",
        cascade="all, delete-orphan",
    )

    campaigns: Mapped[list["Campaign"]] = relationship(
        "Campaign",
        back_populates="business",
        cascade="all, delete-orphan",
    )

    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="business",
    )

    qr_sessions: Mapped[list["QRSession"]] = relationship(
        "QRSession",
        back_populates="business",
    )


class BusinessUser(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "business_users"

    business_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "businesses.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    role: Mapped[BusinessUserRole] = mapped_column(
        SAEnum(
            BusinessUserRole,
            name="business_user_role",
        ),
        nullable=False,
    )

    business: Mapped["Business"] = relationship(
        "Business",
        back_populates="business_users",
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="business_users",
    )

    stamps: Mapped[list["Stamp"]] = relationship(
        "Stamp",
        back_populates="business_user",
    )

    reward_claims: Mapped[list["RewardClaim"]] = relationship(
        "RewardClaim",
        back_populates="business_user",
    )

    __table_args__ = (
        UniqueConstraint(
            "business_id",
            "user_id",
            name="uq_business_users_business_user",
        ),
    )