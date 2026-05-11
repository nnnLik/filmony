from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from services.kinopoisk.client import KinopoiskClient, KinopoiskClientError
from services.kinopoisk.parse_url import KinopoiskUrlParseError, parse_kinopoisk_film_id


class ResolveKinopoiskFilmService:
    def __init__(self, session: AsyncSession, client: KinopoiskClient | None = None) -> None:
        self._session = session
        self._client = client or KinopoiskClient()

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
            film.short_description = payload.short_description
            film.description = payload.description
            await self._session.commit()
            await self._session.refresh(film)
            return film

        film = Film(
            kinopoisk_id=payload.kinopoisk_id,
            title=payload.title,
            year=payload.year,
            poster_url=payload.poster_url,
            genres=payload.genres,
            short_description=payload.short_description,
            description=payload.description,
        )
        self._session.add(film)
        await self._session.commit()
        await self._session.refresh(film)
        return film


__all__ = (
    'KinopoiskClientError',
    'KinopoiskUrlParseError',
    'ResolveKinopoiskFilmService',
)
