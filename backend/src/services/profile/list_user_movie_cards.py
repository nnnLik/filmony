from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import cast
from uuid import UUID

from sqlalchemy import Select, and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.movie_card import MovieCard
from models.movie_card_tag import MovieCardTag

_FAV_CURSOR_PREFIX = 'fav1'


def _encode_favorites_cursor(marked_at: dt.datetime, card_id: int) -> str:
    us = int(marked_at.timestamp() * 1_000_000)
    return f'{_FAV_CURSOR_PREFIX}.{us}.{card_id}'


def _decode_favorites_cursor(cursor: str) -> tuple[dt.datetime, int] | None:
    parts = cursor.split('.')
    if len(parts) != 3 or parts[0] != _FAV_CURSOR_PREFIX:
        return None
    try:
        us = int(parts[1], 10)
        cid = int(parts[2], 10)
    except ValueError:
        return None
    return dt.datetime.fromtimestamp(us / 1_000_000, tz=dt.UTC), cid


@dataclass(frozen=True, slots=True)
class MovieCardListItem:
    id: int
    film_id: int
    film_kinopoisk_id: int
    film_genres: list[str]
    film_title: str
    film_year: int | None
    film_poster_url: str | None
    rating: float
    company: str
    mood_before: str
    mood_after: str
    custom_tags: list[str]
    updated_at: dt.datetime
    is_favorite: bool


@dataclass(frozen=True, slots=True)
class MovieCardPage:
    items: list[MovieCardListItem]
    next_cursor: str | None


def _rows_to_items(
    visible_rows: list[tuple[MovieCard, Film]],
    tags_by_card: dict[int, list[str]],
) -> list[MovieCardListItem]:
    return [
        MovieCardListItem(
            id=card.id,
            film_id=film.id,
            film_kinopoisk_id=film.kinopoisk_id,
            film_genres=list(film.genres or []),
            film_title=film.title,
            film_year=film.year,
            film_poster_url=film.poster_url,
            rating=float(card.rating),
            company=card.company,
            mood_before=card.mood_before,
            mood_after=card.mood_after,
            custom_tags=tags_by_card.get(card.id, []),
            updated_at=card.updated_at,
            is_favorite=bool(card.is_favorite),
        )
        for card, film in visible_rows
    ]


class ListUserMovieCardsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        user_id: UUID,
        cursor: str | None,
        limit: int,
        *,
        favorites_only: bool = False,
    ) -> MovieCardPage:
        if favorites_only:
            return await self._execute_favorites(user_id, cursor, limit)
        return await self._execute_default(user_id, cursor, limit)

    async def _execute_default(
        self, user_id: UUID, cursor: str | None, limit: int
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

        tags_by_card = await self._load_tags(card_ids)
        items = _rows_to_items(visible_rows, tags_by_card)
        next_cursor = str(cast(int, visible_rows[-1][0].id)) if has_more and visible_rows else None
        return MovieCardPage(items=items, next_cursor=next_cursor)

    async def _execute_favorites(
        self, user_id: UUID, cursor: str | None, limit: int
    ) -> MovieCardPage:
        query: Select[tuple[MovieCard, Film]] = (
            select(MovieCard, Film)
            .join(Film, Film.id == MovieCard.film_id)
            .where(
                MovieCard.user_id == user_id,
                MovieCard.is_favorite.is_(True),
                MovieCard.favorite_marked_at.is_not(None),
            )
            .order_by(desc(MovieCard.favorite_marked_at), desc(MovieCard.id))
            .limit(limit + 1)
        )
        if cursor is not None and cursor != '':
            decoded = _decode_favorites_cursor(cursor)
            if decoded is not None:
                cursor_dt, cursor_id = decoded
                query = query.where(
                    or_(
                        MovieCard.favorite_marked_at < cursor_dt,
                        and_(
                            MovieCard.favorite_marked_at == cursor_dt,
                            MovieCard.id < cursor_id,
                        ),
                    )
                )

        rows = (await self._session.execute(query)).all()
        has_more = len(rows) > limit
        visible_rows = rows[:limit]
        card_ids = [card.id for card, _f in visible_rows]

        tags_by_card = await self._load_tags(card_ids)
        items = _rows_to_items(visible_rows, tags_by_card)

        next_cursor: str | None = None
        if has_more and visible_rows:
            last_card = visible_rows[-1][0]
            marked = last_card.favorite_marked_at
            if marked is not None:
                next_cursor = _encode_favorites_cursor(marked, last_card.id)
        return MovieCardPage(items=items, next_cursor=next_cursor)

    async def _load_tags(self, card_ids: list[int]) -> dict[int, list[str]]:
        tags_by_card: dict[int, list[str]] = {}
        if not card_ids:
            return tags_by_card
        tags_rows = (
            await self._session.execute(
                select(MovieCardTag.movie_card_id, MovieCardTag.tag)
                .where(MovieCardTag.movie_card_id.in_(card_ids))
                .order_by(MovieCardTag.movie_card_id, MovieCardTag.tag)
            )
        ).all()
        for cid, tag in tags_rows:
            tags_by_card.setdefault(cid, []).append(tag)
        return tags_by_card

    async def list_all_for_user(self, user_id: UUID) -> list[MovieCardListItem]:
        query: Select[tuple[MovieCard, Film]] = (
            select(MovieCard, Film)
            .join(Film, Film.id == MovieCard.film_id)
            .where(MovieCard.user_id == user_id)
            .order_by(desc(MovieCard.id))
        )
        rows = (await self._session.execute(query)).all()
        card_ids = [card.id for card, _film in rows]

        tags_by_card = await self._load_tags(card_ids)
        return _rows_to_items(rows, tags_by_card)
