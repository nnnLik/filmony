from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from services.profile.compute_weighted_taste_match import (
    ComputeWeightedTasteMatchService,
    TasteMatchBreakdown,
    WeightedTastePeerItem,
)


@dataclass(frozen=True, slots=True)
class TastePeerItem:
    id: UUID
    profile_slug: str
    display_name: str | None
    photo_url: str | None
    similarity_score: float
    score_v2: float
    breakdown: TasteMatchBreakdown
    shared_films_count: int


@dataclass(frozen=True, slots=True)
class UserProfileSocialInsights:
    mutual_subscriptions_count: int
    taste_peers: list[TastePeerItem]


@dataclass
class GetUserProfileSocialInsightsService:
    """Computes mutual subscriptions and weighted taste-peer overlap for profile analytics."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, user_id: UUID) -> UserProfileSocialInsights:
        from sqlalchemy import func, select, union

        from models.user_subscription import UserSubscription

        followers = select(UserSubscription.follower_user_id).where(
            UserSubscription.following_user_id == user_id
        )
        stmt = (
            select(func.count())
            .select_from(UserSubscription)
            .where(
                UserSubscription.follower_user_id == user_id,
                UserSubscription.following_user_id.in_(followers),
            )
        )
        mutual_count = int((await self._session.execute(stmt)).scalar_one())

        weighted_peers = await ComputeWeightedTasteMatchService.build(self._session).execute(
            user_id
        )
        taste_peers = [_to_taste_peer_item(peer) for peer in weighted_peers]

        return UserProfileSocialInsights(
            mutual_subscriptions_count=mutual_count,
            taste_peers=taste_peers,
        )


def _to_taste_peer_item(peer: WeightedTastePeerItem) -> TastePeerItem:
    return TastePeerItem(
        id=peer.id,
        profile_slug=peer.profile_slug,
        display_name=peer.display_name,
        photo_url=peer.photo_url,
        similarity_score=peer.similarity_score,
        score_v2=peer.score_v2,
        breakdown=peer.breakdown,
        shared_films_count=peer.shared_films_count,
    )
