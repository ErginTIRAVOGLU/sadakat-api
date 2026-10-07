from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.businesses.models import BusinessUser
from app.campaign_memberships.models import CampaignMembership
from app.campaigns.models import Campaign
from app.common.enums import (
    CustomerRewardStatus,
    LoyaltyCardStatus,
    QRSessionStatus,
    TransactionType,
)
from app.customer_rewards.models import CustomerReward
from app.loyalty_cards.models import LoyaltyCard
from app.qr_sessions.models import QRSession
from app.stamps.models import Stamp
from app.transactions.models import Transaction
from app.campaigns.service import is_campaign_active


class StampService:

    @staticmethod
    async def earn_stamp(
        db: AsyncSession,
        *,
        qr_session_id: UUID,
        campaign_id: UUID,
        business_user_id: UUID,
    ) -> Stamp:

        now = datetime.now(timezone.utc)

        # ---------------------------------------------------------
        # 1. Lock QR session
        # ---------------------------------------------------------

        qr_result = await db.execute(
            select(QRSession)
            .where(QRSession.id == qr_session_id)
            .with_for_update()
        )

        qr_session = qr_result.scalar_one_or_none()

        if qr_session is None:
            raise ValueError("QR session not found.")

        if qr_session.status != QRSessionStatus.ACTIVE:
            raise ValueError("QR session is no longer active.")

        if qr_session.expires_at <= now:
            raise ValueError("QR session has expired.")

        # ---------------------------------------------------------
        # 2. Load business user
        # ---------------------------------------------------------

        business_user_result = await db.execute(
            select(BusinessUser)
            .where(BusinessUser.id == business_user_id)
        )

        business_user = business_user_result.scalar_one_or_none()

        if business_user is None:
            raise ValueError("Business user not found.")

        # ---------------------------------------------------------
        # 3. Load campaign
        # ---------------------------------------------------------

        campaign_result = await db.execute(
            select(Campaign)
            .where(
                Campaign.id == campaign_id,
                Campaign.business_id == business_user.business_id,
            )
        )

        campaign = campaign_result.scalar_one_or_none()

        if campaign is None:
            raise ValueError(
                "Campaign does not belong to this business."
            )

        # ---------------------------------------------------------
        # 4. Check campaign validity
        # ---------------------------------------------------------

        if not is_campaign_active(campaign, now):
            raise ValueError("Campaign is not active.")

        # ---------------------------------------------------------
        # 5. Find customer's membership
        # ---------------------------------------------------------

        membership_result = await db.execute(
            select(CampaignMembership)
            .where(
                CampaignMembership.campaign_id == campaign.id,
                CampaignMembership.customer_id == qr_session.customer_id,
            )
            .with_for_update()
        )

        membership = membership_result.scalar_one_or_none()

        if membership is None:
            raise ValueError(
                "Customer has not joined this campaign."
            )

        # ---------------------------------------------------------
        # 6. Find active loyalty card
        # ---------------------------------------------------------

        card_result = await db.execute(
            select(LoyaltyCard)
            .where(
                LoyaltyCard.campaign_membership_id == membership.id,
                LoyaltyCard.status == LoyaltyCardStatus.ACTIVE,
            )
            .order_by(LoyaltyCard.card_number.desc())
            .with_for_update()
        )

        loyalty_card = card_result.scalar_one_or_none()

        # ---------------------------------------------------------
        # 7. Create first card if necessary
        # ---------------------------------------------------------

        if loyalty_card is None:

            max_card_result = await db.execute(
                select(LoyaltyCard.card_number)
                .where(
                    LoyaltyCard.campaign_membership_id == membership.id
                )
                .order_by(LoyaltyCard.card_number.desc())
                .limit(1)
            )

            last_card_number = max_card_result.scalar_one_or_none()

            next_card_number = (
                1 if last_card_number is None else last_card_number + 1
            )

            loyalty_card = LoyaltyCard(
                campaign_membership_id=membership.id,
                card_number=next_card_number,
                stamp_count=0,
                status=LoyaltyCardStatus.ACTIVE,
            )

            db.add(loyalty_card)

            await db.flush()

        # ---------------------------------------------------------
        # 8. Safety check
        # ---------------------------------------------------------

        if loyalty_card.stamp_count >= campaign.stamp_target:
            raise ValueError(
                "Loyalty card has already reached the stamp target."
            )

        # ---------------------------------------------------------
        # 9. Create stamp
        # ---------------------------------------------------------

        stamp = Stamp(
            campaign_membership_id=membership.id,
            qr_session_id=qr_session.id,
            business_user_id=business_user.id,
            loyalty_card_id=loyalty_card.id,
        )

        db.add(stamp)

        # ---------------------------------------------------------
        # 10. Increment card
        # ---------------------------------------------------------

        loyalty_card.stamp_count += 1

        # ---------------------------------------------------------
        # 11. Consume QR session
        # ---------------------------------------------------------

        qr_session.status = QRSessionStatus.USED
        qr_session.used_at = now
        qr_session.business_id = business_user.business_id

        # ---------------------------------------------------------
        # 12. Transaction - stamp earned
        # ---------------------------------------------------------

        await db.flush()

        stamp_transaction = Transaction(
            user_id=qr_session.customer.user_id,
            business_id=business_user.business_id,
            type=TransactionType.STAMP_EARNED,
            reference_id=stamp.id,
            details={
                "campaign_id": str(campaign.id),
                "loyalty_card_id": str(loyalty_card.id),
                "stamp_count": loyalty_card.stamp_count,
            },
        )

        db.add(stamp_transaction)

        # ---------------------------------------------------------
        # 13. Card completed?
        # ---------------------------------------------------------

        if loyalty_card.stamp_count == campaign.stamp_target:

            loyalty_card.status = LoyaltyCardStatus.COMPLETED
            loyalty_card.completed_at = now

            # ---------------------------------------------
            # Campaign must have exactly one reward
            # ---------------------------------------------

            reward = campaign.reward

            if reward is None:
                raise ValueError(
                    "Campaign does not have a reward."
                )

            # ---------------------------------------------
            # Create customer reward
            # ---------------------------------------------

            customer_reward = CustomerReward(
                reward_id=reward.id,
                loyalty_card_id=loyalty_card.id,
                status=CustomerRewardStatus.AVAILABLE,
                earned_at=now,
            )

            db.add(customer_reward)

            await db.flush()

            # ---------------------------------------------
            # Transaction - reward earned
            # ---------------------------------------------

            reward_transaction = Transaction(
                user_id=qr_session.customer.user_id,
                business_id=business_user.business_id,
                type=TransactionType.REWARD_EARNED,
                reference_id=customer_reward.id,
                details={
                    "campaign_id": str(campaign.id),
                    "reward_id": str(reward.id),
                    "loyalty_card_id": str(loyalty_card.id),
                },
            )

            db.add(reward_transaction)

            # ---------------------------------------------
            # Create next loyalty card
            # ---------------------------------------------

            next_card = LoyaltyCard(
                campaign_membership_id=membership.id,
                card_number=loyalty_card.card_number + 1,
                stamp_count=0,
                status=LoyaltyCardStatus.ACTIVE,
            )

            db.add(next_card)

        await db.commit()

        await db.refresh(stamp)

        return stamp