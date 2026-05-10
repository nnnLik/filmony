from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import cast
from uuid import UUID

from sqlalchemy import Select, and_, asc, desc, exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select as SASelect

from models.film import Film
from models.movie_card import MovieCard
from models.movie_card_tag import MovieCardTag

_FAV_CURSOR_PREFIX = 'fav1'
_RATING_DESC_PREFIX = 'rtd'
_RATING_ASC_PREFIX = 'rta'

_FILM_TITLE_SEARCH_MAX_LEN = 120


def _normalize_film_title_search(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = raw.strip()
    if len(s) > _FILM_TITLE_SEARCH_MAX_LEN:
        s = s[:_FILM_TITLE_SEARCH_MAX_LEN]
    if s == '':
        return None
    return s


def _film_title_ilike_pattern(needle: str) -> str:
    """Escape ``%``, ``_``, ``\\`` for ILIKE with SQLAlchemy ``escape='\\\\'`` (one backslash in SQL)."""
    esc = needle.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
    return f'%{esc}%'


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


def _encode_rating_desc_cursor(rating: float, card_id: int) -> str:
    # Comma separator: rating uses a dot (e.g. 9.5000) and must not be split as extra segments.
    return f'{_RATING_DESC_PREFIX},{rating:.6f},{card_id}'


def _encode_rating_asc_cursor(rating: float, card_id: int) -> str:
    return f'{_RATING_ASC_PREFIX},{rating:.6f},{card_id}'


def _decode_rating_cursor(cursor: str, *, desc: bool) -> tuple[float, int] | None:
    prefix = _RATING_DESC_PREFIX if desc else _RATING_ASC_PREFIX
    parts = cursor.split(',')
    if len(parts) != 3 or parts[0] != prefix:
        return None
    try:
        r = float(parts[1])
        cid = int(parts[2], 10)
    except ValueError:
        return None
    return r, cid


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
    watch_note: str
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
            watch_note=card.watch_note or '',
            custom_tags=tags_by_card.get(card.id, []),
            updated_at=card.updated_at,
            is_favorite=bool(card.is_favorite),
        )
        for card, film in visible_rows
    ]


class ListUserMovieCardsService:
    """Paginated movie cards for a profile with optional sort and filters."""

    class InvalidCursor(Exception):
        """Cursor does not match the requested sort mode or is malformed."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        user_id: UUID,
        cursor: str | None,
        limit: int,
        *,
        favorites_only: bool = False,
        sort: str = 'recent',
        tags_all: list[str] | None = None,
        year_min: int | None = None,
        year_max: int | None = None,
        company: str | None = None,
        mood_before: str | None = None,
        mood_after: str | None = None,
        film_title_search: str | None = None,
    ) -> MovieCardPage:
        tags = list(tags_all or [])
        title_q = _normalize_film_title_search(film_title_search)
        if favorites_only:
            return await self._execute_favorites(
                user_id,
                cursor,
                limit,
                sort=sort,
                tags_all=tags,
                year_min=year_min,
                year_max=year_max,
                company=company,
                mood_before=mood_before,
                mood_after=mood_after,
                film_title_search=title_q,
            )
        return await self._execute_default(
            user_id,
            cursor,
            limit,
            sort=sort,
            tags_all=tags,
            year_min=year_min,
            year_max=year_max,
            company=company,
            mood_before=mood_before,
            mood_after=mood_after,
            film_title_search=title_q,
        )

    def _apply_filters(
        self,
        query: SASelect[tuple[MovieCard, Film]],
        *,
        tags_all: list[str],
        year_min: int | None,
        year_max: int | None,
        company: str | None,
        mood_before: str | None,
        mood_after: str | None,
        film_title_search: str | None,
    ) -> SASelect[tuple[MovieCard, Film]]:
        for tag in tags_all:
            query = query.where(
                exists(
                    select(1).where(
                        MovieCardTag.movie_card_id == MovieCard.id,
                        MovieCardTag.tag == tag,
                    )
                )
            )
        if year_min is not None or year_max is not None:
            query = query.where(Film.year.is_not(None))
            if year_min is not None:
                query = query.where(Film.year >= year_min)
            if year_max is not None:
                query = query.where(Film.year <= year_max)
        if company is not None:
            query = query.where(MovieCard.company == company)
        if mood_before is not None:
            query = query.where(MovieCard.mood_before == mood_before)
        if mood_after is not None:
            query = query.where(MovieCard.mood_after == mood_after)
        if film_title_search is not None:
            query = query.where(
                Film.title.ilike(_film_title_ilike_pattern(film_title_search), escape='\\'),
            )
        return query

    async def _execute_default(
        self,
        user_id: UUID,
        cursor: str | None,
        limit: int,
        *,
        sort: str,
        tags_all: list[str],
        year_min: int | None,
        year_max: int | None,
        company: str | None,
        mood_before: str | None,
        mood_after: str | None,
        film_title_search: str | None,
    ) -> MovieCardPage:
        query: Select[tuple[MovieCard, Film]] = (
            select(MovieCard, Film)
            .join(Film, Film.id == MovieCard.film_id)
            .where(MovieCard.user_id == user_id)
        )
        query = self._apply_filters(
            query,
            tags_all=tags_all,
            year_min=year_min,
            year_max=year_max,
            company=company,
            mood_before=mood_before,
            mood_after=mood_after,
            film_title_search=film_title_search,
        )

        if sort == 'recent':
            query = query.order_by(desc(MovieCard.id)).limit(limit + 1)
            if cursor is not None and cursor != '':
                try:
                    cid = int(cursor, 10)
                except ValueError as e:
                    raise self.InvalidCursor from e
                query = query.where(MovieCard.id < cid)
        elif sort == 'rating_desc':
            query = query.order_by(desc(MovieCard.rating), desc(MovieCard.id)).limit(limit + 1)
            if cursor is not None and cursor != '':
                decoded = _decode_rating_cursor(cursor, desc=True)
                if decoded is None:
                    raise self.InvalidCursor
                r, cid = decoded
                query = query.where(
                    or_(
                        MovieCard.rating < r,
                        and_(MovieCard.rating == r, MovieCard.id < cid),
                    )
                )
        elif sort == 'rating_asc':
            query = query.order_by(asc(MovieCard.rating), asc(MovieCard.id)).limit(limit + 1)
            if cursor is not None and cursor != '':
                decoded = _decode_rating_cursor(cursor, desc=False)
                if decoded is None:
                    raise self.InvalidCursor
                r, cid = decoded
                query = query.where(
                    or_(
                        MovieCard.rating > r,
                        and_(MovieCard.rating == r, MovieCard.id > cid),
                    )
                )
        else:
            raise ValueError(f'unsupported sort: {sort!r}')

        rows = (await self._session.execute(query)).all()
        has_more = len(rows) > limit
        visible_rows = rows[:limit]
        card_ids = [card.id for card, _film in visible_rows]

        tags_by_card = await self._load_tags(card_ids)
        items = _rows_to_items(visible_rows, tags_by_card)

        next_cursor: str | None = None
        if has_more and visible_rows:
            last_card = visible_rows[-1][0]
            if sort == 'recent':
                next_cursor = str(cast(int, last_card.id))
            elif sort == 'rating_desc':
                next_cursor = _encode_rating_desc_cursor(float(last_card.rating), last_card.id)
            else:
                next_cursor = _encode_rating_asc_cursor(float(last_card.rating), last_card.id)
        return MovieCardPage(items=items, next_cursor=next_cursor)

    async def _execute_favorites(
        self,
        user_id: UUID,
        cursor: str | None,
        limit: int,
        *,
        sort: str,
        tags_all: list[str],
        year_min: int | None,
        year_max: int | None,
        company: str | None,
        mood_before: str | None,
        mood_after: str | None,
        film_title_search: str | None,
    ) -> MovieCardPage:
        query: Select[tuple[MovieCard, Film]] = (
            select(MovieCard, Film)
            .join(Film, Film.id == MovieCard.film_id)
            .where(
                MovieCard.user_id == user_id,
                MovieCard.is_favorite.is_(True),
                MovieCard.favorite_marked_at.is_not(None),
            )
        )
        query = self._apply_filters(
            query,
            tags_all=tags_all,
            year_min=year_min,
            year_max=year_max,
            company=company,
            mood_before=mood_before,
            mood_after=mood_after,
            film_title_search=film_title_search,
        )

        if sort == 'rating_desc':
            query = query.order_by(desc(MovieCard.rating), desc(MovieCard.id)).limit(limit + 1)
            if cursor is not None and cursor != '':
                decoded = _decode_rating_cursor(cursor, desc=True)
                if decoded is None:
                    raise self.InvalidCursor
                r, cid = decoded
                query = query.where(
                    or_(
                        MovieCard.rating < r,
                        and_(MovieCard.rating == r, MovieCard.id < cid),
                    )
                )
        elif sort == 'rating_asc':
            query = query.order_by(asc(MovieCard.rating), asc(MovieCard.id)).limit(limit + 1)
            if cursor is not None and cursor != '':
                decoded = _decode_rating_cursor(cursor, desc=False)
                if decoded is None:
                    raise self.InvalidCursor
                r, cid = decoded
                query = query.where(
                    or_(
                        MovieCard.rating > r,
                        and_(MovieCard.rating == r, MovieCard.id > cid),
                    )
                )
        else:
            query = query.order_by(desc(MovieCard.favorite_marked_at), desc(MovieCard.id)).limit(
                limit + 1
            )
            if cursor is not None and cursor != '':
                decoded = _decode_favorites_cursor(cursor)
                if decoded is None:
                    raise self.InvalidCursor
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
            if sort == 'rating_desc':
                next_cursor = _encode_rating_desc_cursor(float(last_card.rating), last_card.id)
            elif sort == 'rating_asc':
                next_cursor = _encode_rating_asc_cursor(float(last_card.rating), last_card.id)
            else:
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
