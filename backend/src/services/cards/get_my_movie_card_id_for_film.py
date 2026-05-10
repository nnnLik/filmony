from __future__ import annotations

from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.movie_card import MovieCard


class GetMyMovieCardIdForFilmService:
    """Looks up the viewer's rated card for a catalog film, if any."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(session)

    async def execute(self, user_id: UUID, film_id: int) -> int | None:
        q = await self._session.execute(
            select(MovieCard.id).where(MovieCard.user_id == user_id, MovieCard.film_id == film_id)
        )
        return q.scalar_one_or_none()

    async def execute_many(self, user_id: UUID, film_ids: list[int]) -> dict[int, int]:
        """film_id -> movie_card_id for the viewer's rated cards."""
        if not film_ids:
            return {}
        q = await self._session.execute(
            select(MovieCard.film_id, MovieCard.id).where(
                MovieCard.user_id == user_id,
                MovieCard.film_id.in_(film_ids),
            )
        )
        return {int(fid): int(cid) for fid, cid in q.all()}
