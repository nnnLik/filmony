from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from lib.genre_slug import genre_slug
from models.film import Film


@dataclass
class ResolveGenreBySlugService:
    """Resolves a genre slug to the canonical Kinopoisk genre string."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, slug: str) -> str | None:
        normalized_slug = slug.strip().lower()
        if normalized_slug == '':
            return None

        rows = (await self._session.execute(select(Film.genres))).all()

        for (genres,) in rows:
            for genre in genres or []:
                name = str(genre).strip()
                if name == '':
                    continue
                if genre_slug(name) == normalized_slug:
                    return name
        return None
