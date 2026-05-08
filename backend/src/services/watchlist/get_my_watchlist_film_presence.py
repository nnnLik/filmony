from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_watchlist_film import UserWatchlistFilm


@dataclass
class GetMyWatchlistFilmPresenceService:
    """Returns whether the current user listed the film in their watchlist."""

    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: UUID, film_id: int) -> bool:
        row_id = (
            await self._session.execute(
                select(UserWatchlistFilm.id)
                .where(
                    UserWatchlistFilm.user_id == user_id,
                    UserWatchlistFilm.film_id == film_id,
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        return row_id is not None
