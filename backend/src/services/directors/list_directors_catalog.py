from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.user_card import UserCard
from services.directors.get_director_summary import _rated_card_filters


@dataclass(frozen=True, slots=True)
class DirectorCatalogItemDTO:
    kinopoisk_id: int
    name: str
    films_count: int


@dataclass(frozen=True, slots=True)
class DirectorsCatalogPageDTO:
    items: list[DirectorCatalogItemDTO]
    next_cursor: str | None


def _encode_directors_cursor(films_count: int, kinopoisk_id: int) -> str:
    return f'{films_count}:{kinopoisk_id}'


def _decode_directors_cursor(cursor: str) -> tuple[int, int] | None:
    parts = cursor.split(':', 1)
    if len(parts) != 2:
        return None
    try:
        films_count = int(parts[0], 10)
        kinopoisk_id = int(parts[1], 10)
    except ValueError:
        return None
    if films_count < 0 or kinopoisk_id < 1:
        return None
    return films_count, kinopoisk_id


@dataclass
class ListDirectorsCatalogService:
    """Global community catalog of directors with at least one rated film."""

    _session: AsyncSession

    class InvalidCursor(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, cursor: str | None, limit: int) -> DirectorsCatalogPageDTO:
        grouped = (
            select(
                Film.primary_director_kinopoisk_id.label('kinopoisk_id'),
                func.max(Film.primary_director_name).label('name'),
                func.count(func.distinct(Film.id)).label('films_count'),
            )
            .join(UserCard, UserCard.film_id == Film.id)
            .where(
                Film.primary_director_kinopoisk_id.is_not(None),
                *_rated_card_filters(),
            )
            .group_by(Film.primary_director_kinopoisk_id)
        ).subquery()

        query = select(
            grouped.c.kinopoisk_id,
            grouped.c.name,
            grouped.c.films_count,
        ).order_by(
            grouped.c.films_count.desc(),
            grouped.c.kinopoisk_id.desc(),
        )

        if cursor is not None and cursor != '':
            decoded = _decode_directors_cursor(cursor)
            if decoded is None:
                raise self.InvalidCursor
            cursor_count, cursor_kp_id = decoded
            query = query.where(
                (grouped.c.films_count < cursor_count)
                | (
                    (grouped.c.films_count == cursor_count)
                    & (grouped.c.kinopoisk_id < cursor_kp_id)
                ),
            )

        query = query.limit(limit + 1)
        rows = (await self._session.execute(query)).all()
        has_more = len(rows) > limit
        visible = rows[:limit]

        items = [
            DirectorCatalogItemDTO(
                kinopoisk_id=int(row.kinopoisk_id),
                name=str(row.name or f'Режиссёр #{int(row.kinopoisk_id)}').strip(),
                films_count=int(row.films_count),
            )
            for row in visible
        ]

        next_cursor: str | None = None
        if has_more and visible:
            last = visible[-1]
            next_cursor = _encode_directors_cursor(int(last.films_count), int(last.kinopoisk_id))

        return DirectorsCatalogPageDTO(items=items, next_cursor=next_cursor)
