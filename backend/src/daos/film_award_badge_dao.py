from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from models.film_award_badge import FilmAwardBadge, FilmAwardBadgeKind


@dataclass(frozen=True, slots=True)
class FilmAwardBadgeRow:
    kind: FilmAwardBadgeKind
    ceremony_year: int


class FilmAwardBadgeDAO:
    """Persistence gateway for Oscar Best Picture badges on films."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def upsert_badge(
        self,
        *,
        film_id: int,
        kind: FilmAwardBadgeKind,
        ceremony_year: int,
    ) -> FilmAwardBadge:
        stmt = (
            insert(FilmAwardBadge)
            .values(
                film_id=film_id,
                kind=kind.value,
                ceremony_year=ceremony_year,
            )
            .on_conflict_do_nothing(
                constraint='uq_film_award_badge_film_kind_year',
            )
            .returning(FilmAwardBadge)
        )
        result = await self._session.execute(stmt)
        badge = result.scalar_one_or_none()
        if badge is not None:
            return badge

        existing = await self._session.execute(
            select(FilmAwardBadge).where(
                FilmAwardBadge.film_id == film_id,
                FilmAwardBadge.kind == kind.value,
                FilmAwardBadge.ceremony_year == ceremony_year,
            ),
        )
        found = existing.scalar_one()
        return found

    async def list_by_film_id(self, film_id: int) -> list[FilmAwardBadgeRow]:
        by_film = await self.list_by_film_ids([film_id])
        return by_film.get(film_id, [])

    async def list_by_film_ids(self, film_ids: list[int]) -> dict[int, list[FilmAwardBadgeRow]]:
        if not film_ids:
            return {}
        unique_ids = list(dict.fromkeys(film_ids))
        result = await self._session.execute(
            select(
                FilmAwardBadge.film_id,
                FilmAwardBadge.kind,
                FilmAwardBadge.ceremony_year,
            ).where(FilmAwardBadge.film_id.in_(unique_ids)),
        )
        grouped: dict[int, list[FilmAwardBadgeRow]] = {film_id: [] for film_id in unique_ids}
        for film_id, kind, ceremony_year in result.all():
            grouped[int(film_id)].append(
                FilmAwardBadgeRow(
                    kind=FilmAwardBadgeKind(kind),
                    ceremony_year=ceremony_year,
                ),
            )
        return {film_id: _sort_badge_rows(rows) for film_id, rows in grouped.items()}


def _sort_badge_rows(rows: list[FilmAwardBadgeRow]) -> list[FilmAwardBadgeRow]:
    winner = FilmAwardBadgeKind.oscar_best_picture_winner.value

    def sort_key(row: FilmAwardBadgeRow) -> tuple[int, int]:
        kind_rank = 0 if row.kind.value == winner else 1
        return (-row.ceremony_year, kind_rank)

    return sorted(rows, key=sort_key)
