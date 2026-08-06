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
        by_film = await self.execute_many([film_id])
        return by_film.get(film_id, [])

    async def execute_many(self, film_ids: list[int]) -> dict[int, list[FilmAwardBadgeDTO]]:
        grouped = await self._dao.list_by_film_ids(film_ids)
        return {
            film_id: [
                FilmAwardBadgeDTO(kind=row.kind, ceremony_year=row.ceremony_year) for row in rows
            ]
            for film_id, rows in grouped.items()
        }
