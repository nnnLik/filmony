from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from conf import settings
from models.film import Film
from providers.kinopoisk.kinopoisk_provider_transport import KinopoiskProviderTransport
from services.gamification.enrich_film_gamification_metadata import _first_director
from services.kinopoisk.client import KinopoiskClient, KinopoiskClientError
from services.kinopoisk.parse_url import KinopoiskUrlParseError, parse_kinopoisk_film_id
from services.tmdb.sync_film_from_tmdb import SyncFilmFromTmdbService


class ResolveKinopoiskFilmService:
    def __init__(self, session: AsyncSession, client: KinopoiskClient | None = None) -> None:
        self._session = session
        self._client = client or KinopoiskClient()
        self._tmdb_sync = SyncFilmFromTmdbService.build()
        self._kp_transport = KinopoiskProviderTransport()

    async def execute(self, url: str) -> Film:
        kinopoisk_id = parse_kinopoisk_film_id(url)
        existing = await self._session.execute(
            select(Film).where(Film.kinopoisk_id == kinopoisk_id)
        )
        film = existing.scalar_one_or_none()
        payload = await self._client.get_film(kinopoisk_id)
        if film is not None:
            film.title = payload.title
            film.year = payload.year
            film.poster_url = payload.poster_url
            film.genres = payload.genres
            film.countries = payload.countries
            film.short_description = payload.short_description
            film.description = payload.description
            film.imdb_id = payload.imdb_id
            await self._sync_metadata(film)
            await self._session.commit()
            await self._session.refresh(film)
            return film

        film = Film(
            kinopoisk_id=payload.kinopoisk_id,
            title=payload.title,
            year=payload.year,
            poster_url=payload.poster_url,
            genres=payload.genres,
            countries=payload.countries,
            short_description=payload.short_description,
            description=payload.description,
            imdb_id=payload.imdb_id,
        )
        self._session.add(film)
        await self._session.flush()
        await self._sync_metadata(film)
        await self._session.commit()
        await self._session.refresh(film)
        return film

    async def sync_metadata_for_film(self, film: Film) -> None:
        """Sync TMDB + optional KP director metadata onto an existing Film row."""
        await self._sync_metadata(film)

    async def _sync_metadata(self, film: Film) -> None:
        await self._tmdb_sync.execute(
            self._session,
            film,
            imdb_id=film.imdb_id,
            allow_kp_imdb_lookup=False,
        )
        if settings.kinopoisk.enrich_director_id and film.primary_director_kinopoisk_id is None:
            staff = await self._kp_transport.get_staff_by_film_id(film.kinopoisk_id)
            director = _first_director(staff)
            if director is not None:
                film.primary_director_kinopoisk_id = director.staff_id
                if film.primary_director_name is None:
                    film.primary_director_name = director.display_name()


__all__ = (
    'KinopoiskClientError',
    'KinopoiskUrlParseError',
    'ResolveKinopoiskFilmService',
)
