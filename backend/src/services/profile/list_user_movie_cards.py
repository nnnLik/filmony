from __future__ import annotations

from dataclasses import dataclass
from typing import cast
from uuid import UUID

from sqlalchemy import Select, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.movie_card import MovieCard
from models.movie_card_tag import MovieCardTag


@dataclass(frozen=True, slots=True)
class MovieCardListItem:
    id: int
    film_id: int
    film_title: str
    film_year: int | None
    film_poster_url: str | None
    rating: float
    company: str
    mood_before: str
    mood_after: str
    custom_tags: list[str]


@dataclass(frozen=True, slots=True)
class MovieCardPage:
    items: list[MovieCardListItem]
    next_cursor: str | None


class ListUserMovieCardsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        user_id: UUID,
        cursor: str | None,
        limit: int,
    ) -> MovieCardPage:
        query: Select[tuple[MovieCard, Film]] = (
            select(MovieCard, Film)
            .join(Film, Film.id == MovieCard.film_id)
            .where(MovieCard.user_id == user_id)
            .order_by(desc(MovieCard.id))
            .limit(limit + 1)
        )
        if cursor is not None and cursor != '':
            query = query.where(MovieCard.id < int(cursor))

        rows = (await self._session.execute(query)).all()
        has_more = len(rows) > limit
        visible_rows = rows[:limit]
        card_ids = [card.id for card, _film in visible_rows]

        tags_by_card: dict[int, list[str]] = {}
        if card_ids:
            tags_rows = (
                await self._session.execute(
                    select(MovieCardTag.movie_card_id, MovieCardTag.tag)
                    .where(MovieCardTag.movie_card_id.in_(card_ids))
                    .order_by(MovieCardTag.movie_card_id, MovieCardTag.tag)
                )
            ).all()
            for card_id, tag in tags_rows:
                tags_by_card.setdefault(card_id, []).append(tag)

        items = [
            MovieCardListItem(
                id=card.id,
                film_id=film.id,
                film_title=film.title,
                film_year=film.year,
                film_poster_url=film.poster_url,
                rating=float(card.rating),
                company=card.company,
                mood_before=card.mood_before,
                mood_after=card.mood_after,
                custom_tags=tags_by_card.get(card.id, []),
            )
            for card, film in visible_rows
        ]
        next_cursor = str(cast(int, visible_rows[-1][0].id)) if has_more and visible_rows else None
        return MovieCardPage(items=items, next_cursor=next_cursor)
