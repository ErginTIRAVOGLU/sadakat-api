from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.common.enums import QRSessionStatus
from app.common.models import TimestampMixin, UUIDPrimaryKeyMixin
from app.core.database import Base

if TYPE_CHECKING:
    from app.businesses.models import Business
    from app.stamps.models import Stamp
    from app.users.models import CustomerProfile


class QRSession(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "qr_sessions"

    customer_id: Mapped[UUID] = mapped_column(
        ForeignKey(
            "customer_profiles.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )

    token_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    business_id: Mapped[UUID | None] = mapped_column(
        ForeignKey(
            "businesses.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    status: Mapped[QRSessionStatus] = mapped_column(
        SAEnum(
            QRSessionStatus,
            name="qr_session_status",
        ),
        nullable=False,
        default=QRSessionStatus.ACTIVE,
    )

    customer: Mapped["CustomerProfile"] = relationship(
        "CustomerProfile",
        back_populates="qr_sessions",
    )

    business: Mapped["Business | None"] = relationship(
        "Business",
        back_populates="qr_sessions",
    )

    stamp: Mapped["Stamp | None"] = relationship(
        "Stamp",
        back_populates="qr_session",
        uselist=False,
    )