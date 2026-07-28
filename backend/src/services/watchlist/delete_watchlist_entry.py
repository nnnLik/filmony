from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.catalog_item import CatalogProvider
from models.film import Film
from models.watchlist_entry import WatchlistEntry
from services.watchlist.watchlist_card_id import watchlist_card_id_for_provider


@dataclass
class DeleteWatchlistEntryService:
    """Removes a watchlist entry owned by the current user."""

    _session: AsyncSession

    class WatchlistEntryNotFoundError(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute_by_entry_id(self, user_id: UUID, entry_id: int) -> None:
        entry = await self._session.get(WatchlistEntry, entry_id)
        if entry is None or entry.user_id != user_id:
            raise self.WatchlistEntryNotFoundError
        await self._session.delete(entry)
        await self._session.commit()

    async def execute_by_card_id(self, user_id: UUID, card_id: str) -> None:
        entry = (
            await self._session.execute(
                select(WatchlistEntry).where(
                    WatchlistEntry.user_id == user_id,
                    WatchlistEntry.card_id == card_id,
                )
            )
        ).scalar_one_or_none()
        if entry is None:
            raise self.WatchlistEntryNotFoundError
        await self._session.delete(entry)
        await self._session.commit()

    async def execute_by_film_id(self, user_id: UUID, film_id: int) -> None:
        film = await self._session.get(Film, film_id)
        if film is None:
            raise self.WatchlistEntryNotFoundError
        card_id = watchlist_card_id_for_provider(CatalogProvider.kinopoisk, str(film.kinopoisk_id))
        await self.execute_by_card_id(user_id, card_id)
