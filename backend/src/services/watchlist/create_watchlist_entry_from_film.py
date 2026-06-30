from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from services.watchlist.create_watchlist_entry import (
    CreateWatchlistEntryResult,
    CreateWatchlistEntryService,
)


@dataclass(frozen=True, slots=True)
class CreateWatchlistEntryFromFilmResult:
    entry: CreateWatchlistEntryResult
    film: Film


@dataclass
class CreateWatchlistEntryFromFilmService:
    """Creates a watchlist entry from a legacy film id."""

    _session: AsyncSession
    _create_service: CreateWatchlistEntryService

    class FilmNotFoundError(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(
            _session=session,
            _create_service=CreateWatchlistEntryService.build(session),
        )

    async def execute(
        self,
        *,
        actor_user_id: UUID,
        film_id: int,
        created_at: dt.datetime,
    ) -> CreateWatchlistEntryFromFilmResult:
        film = await self._session.get(Film, film_id)
        if film is None:
            raise self.FilmNotFoundError
        card_id = f'kp:{film.kinopoisk_id}'
        provider_meta = {'provider': 'kinopoisk', 'data': {'kp_id': film.kinopoisk_id}}
        entry = await self._create_service.execute(
            actor_user_id=actor_user_id,
            card_id=card_id,
            provider_meta=provider_meta,
            watch_tag='watch_later',
            watch_with_user_id=None,
            created_at=created_at,
        )
        return CreateWatchlistEntryFromFilmResult(entry=entry, film=film)
