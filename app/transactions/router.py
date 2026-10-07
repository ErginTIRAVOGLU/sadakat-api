from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.common.enums import UserRole
from app.core.database import get_db
from app.transactions.schemas import (
    TransactionListResponse,
    TransactionResponse,
)
from app.transactions.service import (
    get_transaction,
    get_user_transactions,
)
from app.users.models import User


router = APIRouter(
    prefix="/transactions",
    tags=["Transactions"],
)


@router.get(
    "",
    response_model=TransactionListResponse,
)
async def get_transactions_endpoint(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TransactionListResponse:
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account required",
        )

    transactions, total = await get_user_transactions(
        db=db,
        user_id=current_user.id,
        skip=skip,
        limit=limit,
    )

    return TransactionListResponse(
        items=[
            TransactionResponse.model_validate(transaction)
            for transaction in transactions
        ],
        total=total,
    )


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
)
async def get_transaction_endpoint(
    transaction_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TransactionResponse:
    transaction = await get_transaction(
        db=db,
        transaction_id=transaction_id,
        user_id=current_user.id,
    )

    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    return TransactionResponse.model_validate(transaction)