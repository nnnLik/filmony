"""Searchable list of the viewer's movie cards for inline ⟦c{id}⟧ picker (title + year only)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.movie_card import MovieCard


@dataclass(frozen=True, slots=True)
class MyMovieCardInlinePickerRow:
    movie_card_id: int
    film_title: str
    film_year: int | None


class ListMyMovieCardsForInlinePickerService:
    """Returns a capped list of the user's cards filtered by film title on the server."""

    _session: AsyncSession

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(session=session)

    async def execute(
        self,
        user_id: UUID,
        *,
        query: str,
        limit: int,
    ) -> list[MyMovieCardInlinePickerRow]:
        cap = max(1, min(limit, 80))
        q = query.strip()
        stmt = (
            select(MovieCard.id, func.coalesce(Film.title, MovieCard.display_title, ''), Film.year)
            .outerjoin(Film, Film.id == MovieCard.film_id)
            .where(MovieCard.user_id == user_id)
            .order_by(desc(MovieCard.created_at), desc(MovieCard.id))
            .limit(cap)
        )
        if q != '':
            pattern = f'%{q}%'
            stmt = stmt.where(
                or_(Film.title.ilike(pattern), MovieCard.display_title.ilike(pattern)),
            )

        rows = (await self._session.execute(stmt)).all()
        return [
            MyMovieCardInlinePickerRow(
                movie_card_id=int(r[0]), film_title=str(r[1]), film_year=r[2]
            )
            for r in rows
        ]
