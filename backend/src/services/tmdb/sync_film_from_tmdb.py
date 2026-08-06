from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from providers.kinopoisk.kinopoisk_provider_transport import KinopoiskProviderTransport
from providers.tmdb.tmdb_mapping import (
    gamification_preview_from_movie,
    normalize_imdb_id,
)
from providers.tmdb.tmdb_provider_transport import TmdbProviderTransport


def _countries_empty(film: Film) -> bool:
    countries = film.countries
    return countries is None or len(countries) == 0


def _has_kp_franchise_key(film: Film) -> bool:
    key = film.franchise_key
    return isinstance(key, str) and key.startswith('kp_franchise:')


@dataclass(frozen=True, slots=True)
class SyncFilmFromTmdbResult:
    synced: bool
    tmdb_id: int | None
    imdb_id: str | None
    reason: str | None = None


@dataclass
class SyncFilmFromTmdbService:
    """Hydrates Film rows from TMDB and maps gamification metadata without touching KP director ids."""

    _transport: TmdbProviderTransport
    _kinopoisk_transport: KinopoiskProviderTransport | None

    class SyncFilmFromTmdbError(Exception):
        pass

    @classmethod
    def build(
        cls,
        *,
        transport: TmdbProviderTransport | None = None,
        kinopoisk_transport: KinopoiskProviderTransport | None = None,
    ) -> Self:
        return cls(
            _transport=transport or TmdbProviderTransport(),
            _kinopoisk_transport=kinopoisk_transport,
        )

    async def execute(
        self,
        session: AsyncSession,
        film: Film,
        *,
        imdb_id: str | None = None,
        tmdb_id: int | None = None,
        force_gamification: bool = False,
        allow_kp_imdb_lookup: bool = False,
    ) -> SyncFilmFromTmdbResult:
        _ = session
        resolved_imdb = normalize_imdb_id(imdb_id or film.imdb_id)
        if resolved_imdb is None and allow_kp_imdb_lookup and self._kinopoisk_transport is not None:
            kp_dto = await self._kinopoisk_transport.get_film_by_id(film.kinopoisk_id)
            resolved_imdb = normalize_imdb_id(kp_dto.imdb_id)
            if resolved_imdb is not None:
                film.imdb_id = resolved_imdb

        resolved_tmdb_id = tmdb_id or film.tmdb_id
        if resolved_tmdb_id is None:
            if resolved_imdb is not None:
                found = await self._transport.find_movie_by_imdb_id(resolved_imdb)
                resolved_tmdb_id = found.first_movie_id()
            if resolved_tmdb_id is None:
                search = await self._transport.search_movie_by_title_year(film.title, film.year)
                resolved_tmdb_id = search.first_movie_id()

        if resolved_tmdb_id is None:
            return SyncFilmFromTmdbResult(
                synced=False,
                tmdb_id=None,
                imdb_id=resolved_imdb,
                reason='tmdb movie not found',
            )

        detail = await self._transport.get_movie_by_id(resolved_tmdb_id)

        if session is not None and film.id is not None:
            conflict_id = await session.scalar(
                select(Film.id).where(
                    Film.tmdb_id == detail.id,
                    Film.id != film.id,
                ),
            )
            if conflict_id is not None:
                return SyncFilmFromTmdbResult(
                    synced=False,
                    tmdb_id=None,
                    imdb_id=resolved_imdb,
                    reason='tmdb_id conflict',
                )

        now = dt.datetime.now(dt.UTC).replace(tzinfo=None)
        film.tmdb_id = detail.id
        film.tmdb_detail_snapshot_json = detail.raw
        film.tmdb_synced_at = now
        if resolved_imdb is not None:
            film.imdb_id = resolved_imdb
        elif detail.imdb_id is not None:
            film.imdb_id = normalize_imdb_id(detail.imdb_id)

        preview = gamification_preview_from_movie(detail, kinopoisk_id=film.kinopoisk_id)
        self._apply_gamification(film, preview, force=force_gamification)

        if film.short_description is None and detail.overview:
            film.short_description = detail.overview[:500]
        if film.description is None and detail.overview:
            film.description = detail.overview

        return SyncFilmFromTmdbResult(
            synced=True,
            tmdb_id=detail.id,
            imdb_id=film.imdb_id,
        )

    def _apply_gamification(
        self,
        film: Film,
        preview,
        *,
        force: bool,
    ) -> None:
        if force or _countries_empty(film):
            film.countries = preview.countries

        if force or film.primary_director_name is None:
            if preview.primary_director_name is not None:
                film.primary_director_name = preview.primary_director_name
            if preview.primary_director_tmdb_id is not None:
                film.primary_director_tmdb_id = preview.primary_director_tmdb_id

        if film.franchise_key is None or (force and not _has_kp_franchise_key(film)):
            film.franchise_key = preview.franchise_key


__all__ = ('SyncFilmFromTmdbResult', 'SyncFilmFromTmdbService')
