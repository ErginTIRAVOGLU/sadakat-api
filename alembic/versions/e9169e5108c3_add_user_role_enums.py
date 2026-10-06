"""add user role enums

Revision ID: e9169e5108c3
Revises: fd0d156f586d
Create Date: 2026-10-06 23:04:08.846715

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "e9169e5108c3"
down_revision: Union[str, Sequence[str], None] = "fd0d156f586d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    business_user_role = postgresql.ENUM(
        "OWNER",
        "MANAGER",
        "STAFF",
        name="business_user_role",
    )

    user_role = postgresql.ENUM(
        "CUSTOMER",
        "BUSINESS",
        "ADMIN",
        name="user_role",
    )

    business_user_role.create(op.get_bind(), checkfirst=True)
    user_role.create(op.get_bind(), checkfirst=True)

    op.alter_column(
        "business_users",
        "role",
        existing_type=sa.VARCHAR(length=20),
        type_=business_user_role,
        existing_nullable=False,
        postgresql_using="role::business_user_role",
    )

    op.alter_column(
        "users",
        "role",
        existing_type=sa.VARCHAR(length=20),
        type_=user_role,
        existing_nullable=False,
        postgresql_using="role::user_role",
    )


def downgrade() -> None:
    """Downgrade schema."""

    op.alter_column(
        "users",
        "role",
        existing_type=postgresql.ENUM(
            "CUSTOMER",
            "BUSINESS",
            "ADMIN",
            name="user_role",
        ),
        type_=sa.VARCHAR(length=20),
        existing_nullable=False,
        postgresql_using="role::text",
    )

    op.alter_column(
        "business_users",
        "role",
        existing_type=postgresql.ENUM(
            "OWNER",
            "MANAGER",
            "STAFF",
            name="business_user_role",
        ),
        type_=sa.VARCHAR(length=20),
        existing_nullable=False,
        postgresql_using="role::text",
    )

    user_role = postgresql.ENUM(
        "CUSTOMER",
        "BUSINESS",
        "ADMIN",
        name="user_role",
    )

    business_user_role = postgresql.ENUM(
        "OWNER",
        "MANAGER",
        "STAFF",
        name="business_user_role",
    )

    user_role.drop(op.get_bind(), checkfirst=True)
    business_user_role.drop(op.get_bind(), checkfirst=True)