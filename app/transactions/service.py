from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.transactions.models import Transaction


async def get_transaction(
    db: AsyncSession,
    transaction_id: UUID,
    user_id: UUID,
) -> Transaction | None:
    result = await db.execute(
        select(Transaction).where(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
        )
    )

    return result.scalar_one_or_none()


async def get_user_transactions(
    db: AsyncSession,
    user_id: UUID,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[Transaction], int]:
    count_result = await db.execute(
        select(func.count(Transaction.id)).where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
        )
    )

    total = count_result.scalar_one()

    result = await db.execute(
        select(Transaction)
        .where(
            Transaction.user_id == user_id,
            Transaction.deleted_at.is_(None),
        )
        .order_by(Transaction.created_at.desc())
        .offset(skip)
        .limit(limit)
    )

    transactions = list(result.scalars().all())

    return transactions, total