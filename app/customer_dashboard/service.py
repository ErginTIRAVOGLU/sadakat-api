from __future__ import annotations

from uuid import UUID

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.campaign_memberships.models import CampaignMembership
from app.customer_rewards.models import CustomerReward
from app.loyalty_cards.models import LoyaltyCard
from app.models import Campaign, Reward
from app.reward_claims.models import RewardClaim
from app.transactions.models import Transaction

from app.common.enums import (
    CustomerRewardStatus,
    LoyaltyCardStatus,
    RewardClaimStatus,
    TransactionType,
)

from app.customer_dashboard.schemas import (
    CustomerDashboardResponse,
    DashboardActiveCardResponse,
    DashboardAvailableRewardResponse,
    DashboardClaimedRewardResponse,
    DashboardCompletedCardResponse,
    DashboardRewardResponse,
    DashboardSummaryResponse,
    DashboardTransactionResponse,
)


class CustomerDashboardService:

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_dashboard(
        self,
        customer_profile_id: UUID,
        user_id: UUID,
    ) -> CustomerDashboardResponse:

        active_cards = await self._get_active_cards(
            customer_profile_id
        )

        available_rewards = await self._get_available_rewards(
            customer_profile_id
        )

        completed_cards = await self._get_completed_cards(
            customer_profile_id
        )

        claimed_rewards = await self._get_claimed_rewards(
            customer_profile_id
        )

        recent_transactions = await self._get_recent_transactions(
            user_id
        )

        return CustomerDashboardResponse(
            summary=self._build_summary(
                active_cards,
                available_rewards,
                completed_cards,
            ),
            active_cards=active_cards,
            available_rewards=available_rewards,
            completed_cards=completed_cards,
            claimed_rewards=claimed_rewards,
            recent_transactions=recent_transactions,
        )

    def _build_summary(
        self,
        active_cards: list[DashboardActiveCardResponse],
        available_rewards: list[DashboardAvailableRewardResponse],
        completed_cards: list[DashboardCompletedCardResponse],
    ) -> DashboardSummaryResponse:

        active_campaigns = len({
            card.campaign_id
            for card in active_cards
        })

        return DashboardSummaryResponse(
            active_campaigns=active_campaigns,
            active_cards=len(active_cards),
            available_rewards=len(available_rewards),
            completed_cards=len(completed_cards),
        )

    async def _get_active_cards(
        self,
        customer_id: UUID,
    ) -> list[DashboardActiveCardResponse]:

        stmt = (
            select(LoyaltyCard)
            .join(LoyaltyCard.campaign_membership)
            .join(CampaignMembership.campaign)
            .join(CampaignMembership.customer)
            .options(
                joinedload(
                    LoyaltyCard.campaign_membership
                )
                .joinedload(
                    CampaignMembership.campaign
                )
                .joinedload(
                    Campaign.business
                )
            )
            .where(
                CampaignMembership.customer_id == customer_id,
                LoyaltyCard.status == LoyaltyCardStatus.ACTIVE,
            )
            .order_by(
                desc(LoyaltyCard.created_at)
            )
        )

        result = await self.session.execute(stmt)

        cards = result.scalars().unique().all()

        response = []

        for card in cards:
            membership = card.campaign_membership
            campaign = membership.campaign
            business = campaign.business

            required_stamps = campaign.stamp_target
            current_stamps = card.stamp_count

            remaining_stamps = max(
                required_stamps - current_stamps,
                0,
            )

            progress = (
                int(
                    current_stamps
                    / required_stamps
                    * 100
                )
                if required_stamps > 0
                else 0
            )

            response.append(
                DashboardActiveCardResponse(
                    id=card.id,
                    campaign_id=campaign.id,
                    campaign_name=campaign.name,
                    business_id=business.id,
                    business_name=business.name,
                    card_number=card.card_number,
                    required_stamps=required_stamps,
                    current_stamps=current_stamps,
                    remaining_stamps=remaining_stamps,
                    progress=min(progress, 100),
                    joined_at=membership.joined_at,
                )
            )

        return response

    async def _get_available_rewards(
        self,
        customer_id: UUID,
    ) -> list[DashboardAvailableRewardResponse]:

        stmt = (
            select(CustomerReward)
            .join(CustomerReward.loyalty_card)
            .join(LoyaltyCard.campaign_membership)
            .join(CustomerReward.reward)
            .join(CampaignMembership.customer)
            .options(
                joinedload(
                    CustomerReward.reward
                )
                .joinedload(
                    Reward.campaign
                )
                .joinedload(
                    Campaign.business
                )
            )
            .where(
                CampaignMembership.customer_id == customer_id,
                CustomerReward.status
                == CustomerRewardStatus.AVAILABLE,
            )
            .order_by(
                desc(CustomerReward.earned_at)
            )
        )

        result = await self.session.execute(stmt)

        rewards = result.scalars().unique().all()

        response = []

        for customer_reward in rewards:
            reward = customer_reward.reward
            campaign = reward.campaign
            business = campaign.business

            response.append(
                DashboardAvailableRewardResponse(
                    id=customer_reward.id,
                    campaign_id=campaign.id,
                    campaign_name=campaign.name,
                    business_id=business.id,
                    business_name=business.name,
                    reward=DashboardRewardResponse(
                        id=reward.id,
                        name=reward.name,
                        description=reward.description,
                        reward_type=reward.reward_type.value,
                        reward_value=reward.reward_value,
                    ),
                    earned_at=customer_reward.earned_at, 
                )
            )

        return response

    async def _get_completed_cards(
        self,
        customer_id: UUID,
    ) -> list[DashboardCompletedCardResponse]:

        stmt = (
            select(LoyaltyCard)
            .join(LoyaltyCard.campaign_membership)
            .join(CampaignMembership.campaign)
            .join(CampaignMembership.customer)
            .options(
                joinedload(
                    LoyaltyCard.campaign_membership
                )
                .joinedload(
                    CampaignMembership.campaign
                )
                .joinedload(
                    Campaign.business
                ),
                joinedload(
                    LoyaltyCard.customer_rewards
                )
                .joinedload(
                    CustomerReward.reward
                ),
            )
            .where(
                CampaignMembership.customer_id == customer_id,
                LoyaltyCard.status
                == LoyaltyCardStatus.COMPLETED,
            )
            .order_by(
                desc(LoyaltyCard.completed_at)
            )
        )

        result = await self.session.execute(stmt)

        cards = result.scalars().unique().all()

        response = []

        for card in cards:
            membership = card.campaign_membership
            campaign = membership.campaign
            business = campaign.business

            reward = None

            if card.customer_rewards:
                customer_reward = card.customer_rewards[0]
                reward_model = customer_reward.reward

                reward = DashboardRewardResponse(
                    id=reward_model.id,
                    name=reward_model.name,
                    description=reward_model.description,
                    reward_type=reward_model.reward_type.value,
                    reward_value=reward_model.reward_value,
                )

            response.append(
                DashboardCompletedCardResponse(
                    id=card.id,
                    campaign_id=campaign.id,
                    campaign_name=campaign.name,
                    business_id=business.id,
                    business_name=business.name,
                    card_number=card.card_number,
                    required_stamps=campaign.stamp_target,
                    completed_stamps=card.stamp_count,
                    completed_at=card.completed_at,
                    reward=reward,
                )
            )

        return response

    async def _get_claimed_rewards(
        self,
        customer_id: UUID,
    ) -> list[DashboardClaimedRewardResponse]:

        stmt = (
            select(RewardClaim)
            .join(RewardClaim.customer_reward)
            .join(CustomerReward.loyalty_card)
            .join(LoyaltyCard.campaign_membership)
            .join(CustomerReward.reward)
            .join(CampaignMembership.customer)
            .options(
                joinedload(
                    RewardClaim.customer_reward
                )
                .joinedload(
                    CustomerReward.reward
                )
                .joinedload(
                    Reward.campaign
                )
                .joinedload(
                    Campaign.business
                )
            )
            .where(
                CampaignMembership.customer_id == customer_id,
                RewardClaim.status
                == RewardClaimStatus.USED,
            )
            .order_by(
                desc(RewardClaim.claimed_at)
            )
        )

        result = await self.session.execute(stmt)

        claims = result.scalars().unique().all()

        response = []

        for claim in claims:
            customer_reward = claim.customer_reward
            reward = customer_reward.reward
            campaign = reward.campaign
            business = campaign.business

            response.append(
                DashboardClaimedRewardResponse(
                    id=customer_reward.id,
                    campaign_id=campaign.id,
                    campaign_name=campaign.name,
                    business_id=business.id,
                    business_name=business.name,
                    reward=DashboardRewardResponse(
                        id=reward.id,
                        name=reward.name,
                        description=reward.description,
                        reward_type=reward.reward_type.value,
                        reward_value=reward.reward_value,
                    ),
                    earned_at=customer_reward.earned_at,
                    claimed_at=claim.claimed_at,
                )
            )

        return response

    async def _get_recent_transactions(
        self,
        user_id: UUID,
    ) -> list[DashboardTransactionResponse]:

        stmt = (
            select(Transaction)
            .options(
                joinedload(Transaction.business)
            )
            .where(
                Transaction.user_id == user_id,
            )
            .order_by(
                desc(Transaction.created_at)
            )
            .limit(20)
        )

        result = await self.session.execute(stmt)

        transactions = result.scalars().all()

        response = []

        for transaction in transactions:
            title, description = self._get_transaction_text(
                transaction
            )

            response.append(
                DashboardTransactionResponse(
                    id=transaction.id,
                    type=transaction.type.value,
                    title=title,
                    description=description,
                    business_id=transaction.business_id,
                    business_name=(
                        transaction.business.name
                        if transaction.business
                        else None
                    ),
                    created_at=transaction.created_at,
                )
            )

        return response

    def _get_transaction_text(
        self,
        transaction: Transaction,
    ) -> tuple[str, str | None]:

        transaction_type = transaction.type

        if transaction_type == TransactionType.CAMPAIGN_JOINED:
            return (
                "Kampanyaya katıldın",
                "Yeni bir sadakat kampanyasına katıldın.",
            )

        if transaction_type == TransactionType.STAMP_EARNED:
            return (
                "Damga kazandın",
                "Sadakat kartına yeni bir damga eklendi.",
            )

        if transaction_type == TransactionType.REWARD_EARNED:
            return (
                "Ödül kazandın",
                "Sadakat kartını tamamladın ve yeni bir ödül kazandın.",
            )

        if transaction_type == TransactionType.REWARD_USED:
            return (
                "Ödülünü kullandın",
                "Kazandığın ödül başarıyla kullanıldı.",
            )

        if transaction_type == TransactionType.QR_SCANNED:
            return (
                "QR kod tarandı",
                "Sadakat işlemi için QR kodun tarandı.",
            )

        return (
            "İşlem gerçekleşti",
            None,
        )