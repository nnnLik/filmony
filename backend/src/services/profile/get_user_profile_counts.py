from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.movie_card import MovieCard
from models.user_subscription import UserSubscription


@dataclass(frozen=True, slots=True)
class UserProfileCounts:
    movie_cards: int
    friends: int
    followers_count: int
    following_count: int


class GetUserProfileCountsService:
    """Aggregate counts for profile headers."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: UUID) -> UserProfileCounts:
        cards_result = await self._session.execute(
            select(func.count(MovieCard.id)).where(MovieCard.user_id == user_id)
        )
        cards_count = int(cards_result.scalar_one())
        followers_result = await self._session.execute(
            select(func.count(UserSubscription.id)).where(
                UserSubscription.following_user_id == user_id
            )
        )
        following_result = await self._session.execute(
            select(func.count(UserSubscription.id)).where(
                UserSubscription.follower_user_id == user_id
            )
        )
        return UserProfileCounts(
            movie_cards=cards_count,
            friends=0,
            followers_count=int(followers_result.scalar_one()),
            following_count=int(following_result.scalar_one()),
        )
