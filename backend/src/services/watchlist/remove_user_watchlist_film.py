from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_watchlist_film import UserWatchlistFilm


@dataclass
class RemoveUserWatchlistFilmService:
    """Removes a film from the current user's watchlist."""

    _session: AsyncSession

    class WatchlistEntryNotFoundError(Exception):
        pass

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: UUID, film_id: int) -> None:
        result = await self._session.execute(
            delete(UserWatchlistFilm).where(
                UserWatchlistFilm.user_id == user_id,
                UserWatchlistFilm.film_id == film_id,
            )
        )
        if result.rowcount == 0:
            raise self.WatchlistEntryNotFoundError
        await self._session.commit()
