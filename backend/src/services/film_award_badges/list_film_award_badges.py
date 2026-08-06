from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from daos.film_award_badge_dao import FilmAwardBadgeDAO
from models.film_award_badge import FilmAwardBadgeKind


@dataclass(frozen=True, slots=True)
class FilmAwardBadgeDTO:
    kind: FilmAwardBadgeKind
    ceremony_year: int


@dataclass
class ListFilmAwardBadgesService:
    """Returns Oscar Best Picture badges for a film, ordered for display."""

    _dao: FilmAwardBadgeDAO

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_dao=FilmAwardBadgeDAO(session))

    async def execute(self, film_id: int) -> list[FilmAwardBadgeDTO]:
        rows = await self._dao.list_by_film_id(film_id)
        return [FilmAwardBadgeDTO(kind=row.kind, ceremony_year=row.ceremony_year) for row in rows]
