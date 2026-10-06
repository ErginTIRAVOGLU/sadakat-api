from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any


from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship


from app.common.enums.transaction import TransactionType
from app.common.models import UUIDPrimaryKeyMixin, TimestampMixin
from app.core.database import Base


if TYPE_CHECKING:
    from app.businesses.models import Business
    from app.users.models import User

class Transaction(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "transactions"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "users.id",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    business_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "businesses.id",
            ondelete="SET NULL",
        ),
        nullable=True,
        index=True,
    )

    type: Mapped[TransactionType] = mapped_column(
        SQLEnum(
            TransactionType,
            name="transaction_type",
        ),
        nullable=False,
        index=True,
    )

    reference_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        nullable=True,
        index=True,
    )

    details: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="transactions",
    )

    business: Mapped["Business | None"] = relationship(
        "Business",
        back_populates="transactions",
    )