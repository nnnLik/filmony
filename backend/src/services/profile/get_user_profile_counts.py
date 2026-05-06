from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.movie_card import MovieCard


@dataclass(frozen=True, slots=True)
class UserProfileCounts:
    movie_cards: int
    friends: int


class GetUserProfileCountsService:
    """Aggregate counts for profile headers."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: UUID) -> UserProfileCounts:
        cards_result = await self._session.execute(
            select(func.count(MovieCard.id)).where(MovieCard.user_id == user_id)
        )
        cards_count = int(cards_result.scalar_one())
        return UserProfileCounts(movie_cards=cards_count, friends=0)
