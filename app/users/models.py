import uuid
from datetime import datetime
from typing import TYPE_CHECKING 

from sqlalchemy import Boolean, ForeignKey, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from sqlalchemy import Enum as SAEnum

from app.common.enums import UserRole
from app.common.models import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base


if TYPE_CHECKING:
    from app.businesses.models import BusinessUser
    from app.campaign_memberships.models import CampaignMembership
    from app.qr_sessions.models import QRSession
    from app.reward_claims.models import RewardClaim
    from app.transactions.models import Transaction

class User(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[UserRole] = mapped_column(
        SAEnum(
            UserRole,
            name="user_role",
        ),
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        nullable=False,
    )

    email_verified: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        nullable=False,
    )

    last_login_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    customer_profile: Mapped["CustomerProfile | None"] = relationship(
        "CustomerProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )

    business_users: Mapped[list["BusinessUser"]] = relationship(
        "BusinessUser",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    
    transactions: Mapped[list["Transaction"]] = relationship(
        "Transaction",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    
class CustomerProfile(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "customer_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),        
        ForeignKey(
            "users.id", 
            ondelete="CASCADE"
        ),
        nullable=False,
        unique=True,
        index=True,
    )

    first_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    last_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    phone: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    avatar_url: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="customer_profile",
    )
 
    campaign_memberships: Mapped[list["CampaignMembership"]] = relationship(
        "CampaignMembership",
        back_populates="customer",
        cascade="all, delete-orphan",
    )

    qr_sessions: Mapped[list["QRSession"]] = relationship(
        "QRSession",
        back_populates="customer",
    )

    reward_claims: Mapped[list["RewardClaim"]] = relationship(
        "RewardClaim",
        back_populates="customer",
    )