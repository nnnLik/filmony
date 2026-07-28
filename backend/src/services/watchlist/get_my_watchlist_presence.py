from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from models.watchlist_entry import WatchlistEntry
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class GetMyWatchlistPresenceService:
    """Returns whether the current user has a watchlist entry for the given card_id."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, user_id: UUID, card_id: str) -> bool:
        row_id = (
            await self._session.execute(
                select(WatchlistEntry.id)
                .where(
                    WatchlistEntry.user_id == user_id,
                    WatchlistEntry.card_id == card_id,
                )
                .limit(1)
            )
        ).scalar_one_or_none()
        return row_id is not None
