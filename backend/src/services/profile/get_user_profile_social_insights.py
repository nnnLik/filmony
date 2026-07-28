from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import desc, func, select, union
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from models.user_card import UserCard
from models.user_subscription import UserSubscription

TASTE_PEERS_LIMIT = 5


@dataclass(frozen=True, slots=True)
class TastePeerItem:
    id: UUID
    profile_slug: str
    display_name: str | None
    photo_url: str | None
    similarity_score: float
    shared_films_count: int


@dataclass(frozen=True, slots=True)
class UserProfileSocialInsights:
    mutual_subscriptions_count: int
    taste_peers: list[TastePeerItem]


@dataclass
class GetUserProfileSocialInsightsService:
    """Computes mutual subscriptions and taste-peer overlap for profile analytics."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, user_id: UUID) -> UserProfileSocialInsights:
        mutual_count = await self._count_mutual_subscriptions(user_id)
        taste_peers = await self._load_taste_peers(user_id)
        return UserProfileSocialInsights(
            mutual_subscriptions_count=mutual_count,
            taste_peers=taste_peers,
        )

    async def _count_mutual_subscriptions(self, user_id: UUID) -> int:
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
        return int((await self._session.execute(stmt)).scalar_one())

    async def _load_taste_peers(self, user_id: UUID) -> list[TastePeerItem]:
        profile_film_ids = (
            (
                await self._session.execute(
                    select(UserCard.film_id).where(
                        UserCard.user_id == user_id,
                        UserCard.is_planned.is_(False),
                        UserCard.film_id.is_not(None),
                    )
                )
            )
            .scalars()
            .all()
        )
        profile_film_set = {int(fid) for fid in profile_film_ids}
        profile_film_count = len(profile_film_set)
        if profile_film_count == 0:
            return []

        followers = select(UserSubscription.follower_user_id.label('peer_id')).where(
            UserSubscription.following_user_id == user_id
        )
        following = select(UserSubscription.following_user_id.label('peer_id')).where(
            UserSubscription.follower_user_id == user_id
        )
        network = union(followers, following).subquery()

        overlap_rows = (
            await self._session.execute(
                select(
                    UserCard.user_id,
                    func.count(func.distinct(UserCard.film_id)).label('shared_count'),
                )
                .join(network, network.c.peer_id == UserCard.user_id)
                .where(
                    UserCard.is_planned.is_(False),
                    UserCard.film_id.in_(profile_film_set),
                )
                .group_by(UserCard.user_id)
                .order_by(
                    desc(func.count(func.distinct(UserCard.film_id))),
                    UserCard.user_id,
                )
                .limit(TASTE_PEERS_LIMIT)
            )
        ).all()
        if not overlap_rows:
            return []

        peer_ids = [row[0] for row in overlap_rows]
        peer_film_counts = dict(
            (
                await self._session.execute(
                    select(UserCard.user_id, func.count(UserCard.id))
                    .where(
                        UserCard.user_id.in_(peer_ids),
                        UserCard.is_planned.is_(False),
                    )
                    .group_by(UserCard.user_id)
                )
            ).all()
        )

        users_by_id = {
            user.id: user
            for user in (await self._session.execute(select(User).where(User.id.in_(peer_ids))))
            .scalars()
            .all()
        }

        peers: list[TastePeerItem] = []
        for peer_id, shared_count in overlap_rows:
            user = users_by_id.get(peer_id)
            if user is None:
                continue
            shared = int(shared_count)
            peer_total = int(peer_film_counts.get(peer_id, 0))
            union_size = profile_film_count + peer_total - shared
            similarity = round(shared / union_size, 3) if union_size > 0 else 0.0
            peers.append(
                TastePeerItem(
                    id=user.id,
                    profile_slug=user.profile_slug,
                    display_name=user.display_name,
                    photo_url=user.photo_url,
                    similarity_score=similarity,
                    shared_films_count=shared,
                )
            )
        return peers
