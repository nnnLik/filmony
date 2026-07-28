from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from services.search.ilike_escape import escape_ilike_pattern


@dataclass(frozen=True, slots=True)
class CatalogFilmSearchHit:
    """Minimal film row for catalog search results."""

    id: int
    kinopoisk_id: int
    title: str
    year: int | None
    poster_url: str | None
    genres: list[str]


@dataclass
class SearchCatalogFilmsService:
    """Finds films in the local catalog whose title matches a free-text query."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, query: str, limit: int) -> list[CatalogFilmSearchHit]:
        pattern = f'%{escape_ilike_pattern(query)}%'
        stmt = (
            select(Film)
            .where(Film.title.ilike(pattern, escape='\\'))
            .order_by(Film.title.asc(), Film.id.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [
            CatalogFilmSearchHit(
                id=f.id,
                kinopoisk_id=f.kinopoisk_id,
                title=f.title,
                year=f.year,
                poster_url=f.poster_url,
                genres=list(f.genres or []),
            )
            for f in rows
        ]
