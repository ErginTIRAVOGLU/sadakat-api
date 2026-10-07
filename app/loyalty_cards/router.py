from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.common.enums import UserRole
from app.core.database import get_db
from app.loyalty_cards.schemas import LoyaltyCardResponse
from app.loyalty_cards.service import (
    get_customer_loyalty_card,
    get_customer_loyalty_cards,
)
from app.users.models import CustomerProfile, User


router = APIRouter(
    prefix="/loyalty-cards",
    tags=["Loyalty Cards"],
)


async def get_current_customer(
    current_user: User,
    db: AsyncSession,
) -> CustomerProfile:
    if current_user.role != UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer account required",
        )

    result = await db.execute(
        select(CustomerProfile).where(
            CustomerProfile.user_id == current_user.id,
        )
    )

    customer = result.scalar_one_or_none()

    if customer is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Customer profile not found",
        )

    return customer


@router.get(
    "",
    response_model=list[LoyaltyCardResponse],
)
async def list_loyalty_cards_endpoint(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[LoyaltyCardResponse]:
    customer = await get_current_customer(
        current_user=current_user,
        db=db,
    )

    cards = await get_customer_loyalty_cards(
        db=db,
        customer=customer,
    )

    return [
        LoyaltyCardResponse.model_validate(card)
        for card in cards
    ]


@router.get(
    "/{card_id}",
    response_model=LoyaltyCardResponse,
)
async def get_loyalty_card_endpoint(
    card_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> LoyaltyCardResponse:
    customer = await get_current_customer(
        current_user=current_user,
        db=db,
    )

    card = await get_customer_loyalty_card(
        db=db,
        customer=customer,
        card_id=card_id,
    )

    return LoyaltyCardResponse.model_validate(card)