from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import cast
from uuid import UUID

from sqlalchemy import Select, and_, asc, desc, exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import Select as SASelect

from models.card_tag import CardTag
from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from models.game import Game
from models.user_card import UserCard
from models.user_card_category import DEFAULT_USER_CARD_CATEGORY_NAME, UserCardCategory
from services.cards.card_catalog_release_fields import universal_release_year_date

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
class UserCardListItem:
    id: int
    provider: CatalogProvider
    external_id: str | None
    film_id: int | None
    film_kinopoisk_id: int | None
    film_genres: list[str]
    film_title: str
    film_year: int | None
    release_year: int | None
    release_date: str | None
    film_poster_url: str | None
    catalog_item_id: int | None
    display_title: str
    display_cover_url: str | None
    rating: float
    company: str
    mood_before: str
    mood_after: str
    watch_note: str
    custom_tags: list[str]
    updated_at: dt.datetime
    is_favorite: bool
    category_id: int
    category_name: str


@dataclass(frozen=True, slots=True)
class UserCardListPage:
    items: list[UserCardListItem]
    next_cursor: str | None


def _rows_to_items(
    visible_rows: list[tuple[UserCard, Film | None, Game | None]],
    tags_by_card: dict[int, list[str]],
    category_name_by_id: dict[int, str],
) -> list[UserCardListItem]:
    items: list[UserCardListItem] = []
    for card, film, game in visible_rows:
        display_title = (card.display_title or '').strip()
        film_title = film.title if film is not None else (display_title or 'Untitled')
        if not display_title:
            display_title = film_title
        poster = film.poster_url if film is not None else card.display_cover_url
        cid = int(card.category_id)
        film_year_val = film.year if film is not None else None
        release_year, release_date = universal_release_year_date(
            film_year=film_year_val,
            game_released=game.released if game is not None else None,
        )
        items.append(
            UserCardListItem(
                id=card.id,
                provider=card.provider,
                external_id=card.external_id,
                film_id=film.id if film is not None else None,
                film_kinopoisk_id=film.kinopoisk_id if film is not None else None,
                film_genres=list(film.genres or []) if film is not None else [],
                film_title=film_title,
                film_year=film_year_val,
                release_year=release_year,
                release_date=release_date,
                film_poster_url=poster,
                catalog_item_id=card.catalog_item_id,
                display_title=display_title,
                display_cover_url=card.display_cover_url,
                rating=float(card.rating),
                company=card.company,
                mood_before=card.mood_before,
                mood_after=card.mood_after,
                watch_note=card.watch_note or '',
                custom_tags=tags_by_card.get(card.id, []),
                updated_at=card.updated_at,
                is_favorite=bool(card.is_favorite),
                category_id=cid,
                category_name=category_name_by_id.get(cid, DEFAULT_USER_CARD_CATEGORY_NAME),
            )
        )
    return items


class ListUserCardsService:
    """Paginated movie cards for a profile with optional sort and filters."""

    class InvalidCursor(Exception):
        """Cursor does not match the requested sort mode or is malformed."""

    class InvalidCategoryFilter(Exception):
        """category_id does not belong to the profile user."""

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
        category_id: int | None = None,
    ) -> UserCardListPage:
        tags = list(tags_all or [])
        title_q = _normalize_film_title_search(film_title_search)
        if category_id is not None:
            owns = (
                await self._session.execute(
                    select(UserCardCategory.id).where(
                        UserCardCategory.id == category_id,
                        UserCardCategory.user_id == user_id,
                    )
                )
            ).scalar_one_or_none()
            if owns is None:
                raise self.InvalidCategoryFilter
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
                category_id=category_id,
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
            category_id=category_id,
        )

    def _apply_filters(
        self,
        query: SASelect[tuple[UserCard, Film | None, Game | None]],
        *,
        tags_all: list[str],
        year_min: int | None,
        year_max: int | None,
        company: str | None,
        mood_before: str | None,
        mood_after: str | None,
        film_title_search: str | None,
        category_id: int | None,
    ) -> SASelect[tuple[UserCard, Film | None, Game | None]]:
        for tag in tags_all:
            query = query.where(
                exists(
                    select(1).where(
                        CardTag.card_id == UserCard.id,
                        CardTag.tag == tag,
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
            query = query.where(UserCard.company == company)
        if mood_before is not None:
            query = query.where(UserCard.mood_before == mood_before)
        if mood_after is not None:
            query = query.where(UserCard.mood_after == mood_after)
        if film_title_search is not None:
            pattern = _film_title_ilike_pattern(film_title_search)
            query = query.where(
                or_(
                    Film.title.ilike(pattern, escape='\\'),
                    UserCard.display_title.ilike(pattern, escape='\\'),
                )
            )
        if category_id is not None:
            query = query.where(UserCard.category_id == category_id)
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
        category_id: int | None,
    ) -> UserCardListPage:
        query: Select[tuple[UserCard, Film | None, Game | None]] = (
            select(UserCard, Film, Game)
            .select_from(UserCard)
            .outerjoin(CatalogItem, CatalogItem.id == UserCard.catalog_item_id)
            .outerjoin(Film, Film.id == func.coalesce(UserCard.film_id, CatalogItem.film_id))
            .outerjoin(Game, Game.id == CatalogItem.game_id)
            .where(UserCard.user_id == user_id)
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
            category_id=category_id,
        )

        if sort == 'recent':
            query = query.order_by(desc(UserCard.id)).limit(limit + 1)
            if cursor is not None and cursor != '':
                try:
                    cid = int(cursor, 10)
                except ValueError as e:
                    raise self.InvalidCursor from e
                query = query.where(UserCard.id < cid)
        elif sort == 'rating_desc':
            query = query.order_by(desc(UserCard.rating), desc(UserCard.id)).limit(limit + 1)
            if cursor is not None and cursor != '':
                decoded = _decode_rating_cursor(cursor, desc=True)
                if decoded is None:
                    raise self.InvalidCursor
                r, cid = decoded
                query = query.where(
                    or_(
                        UserCard.rating < r,
                        and_(UserCard.rating == r, UserCard.id < cid),
                    )
                )
        elif sort == 'rating_asc':
            query = query.order_by(asc(UserCard.rating), asc(UserCard.id)).limit(limit + 1)
            if cursor is not None and cursor != '':
                decoded = _decode_rating_cursor(cursor, desc=False)
                if decoded is None:
                    raise self.InvalidCursor
                r, cid = decoded
                query = query.where(
                    or_(
                        UserCard.rating > r,
                        and_(UserCard.rating == r, UserCard.id > cid),
                    )
                )
        else:
            raise ValueError(f'unsupported sort: {sort!r}')

        rows = (await self._session.execute(query)).all()
        has_more = len(rows) > limit
        visible_rows = rows[:limit]
        card_ids = [card.id for card, _film, _game in visible_rows]

        tags_by_card = await self._load_tags(card_ids)
        cat_names = await self._load_category_names(
            list({int(c.category_id) for c, _, _ in visible_rows})
        )
        items = _rows_to_items(visible_rows, tags_by_card, cat_names)

        next_cursor: str | None = None
        if has_more and visible_rows:
            last_card = visible_rows[-1][0]
            if sort == 'recent':
                next_cursor = str(cast(int, last_card.id))
            elif sort == 'rating_desc':
                next_cursor = _encode_rating_desc_cursor(float(last_card.rating), last_card.id)
            else:
                next_cursor = _encode_rating_asc_cursor(float(last_card.rating), last_card.id)
        return UserCardListPage(items=items, next_cursor=next_cursor)

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
        category_id: int | None,
    ) -> UserCardListPage:
        query: Select[tuple[UserCard, Film | None, Game | None]] = (
            select(UserCard, Film, Game)
            .select_from(UserCard)
            .outerjoin(CatalogItem, CatalogItem.id == UserCard.catalog_item_id)
            .outerjoin(Film, Film.id == func.coalesce(UserCard.film_id, CatalogItem.film_id))
            .outerjoin(Game, Game.id == CatalogItem.game_id)
            .where(
                UserCard.user_id == user_id,
                UserCard.is_favorite.is_(True),
                UserCard.favorite_marked_at.is_not(None),
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
            category_id=category_id,
        )

        if sort == 'rating_desc':
            query = query.order_by(desc(UserCard.rating), desc(UserCard.id)).limit(limit + 1)
            if cursor is not None and cursor != '':
                decoded = _decode_rating_cursor(cursor, desc=True)
                if decoded is None:
                    raise self.InvalidCursor
                r, cid = decoded
                query = query.where(
                    or_(
                        UserCard.rating < r,
                        and_(UserCard.rating == r, UserCard.id < cid),
                    )
                )
        elif sort == 'rating_asc':
            query = query.order_by(asc(UserCard.rating), asc(UserCard.id)).limit(limit + 1)
            if cursor is not None and cursor != '':
                decoded = _decode_rating_cursor(cursor, desc=False)
                if decoded is None:
                    raise self.InvalidCursor
                r, cid = decoded
                query = query.where(
                    or_(
                        UserCard.rating > r,
                        and_(UserCard.rating == r, UserCard.id > cid),
                    )
                )
        else:
            query = query.order_by(desc(UserCard.favorite_marked_at), desc(UserCard.id)).limit(
                limit + 1
            )
            if cursor is not None and cursor != '':
                decoded = _decode_favorites_cursor(cursor)
                if decoded is None:
                    raise self.InvalidCursor
                cursor_dt, cursor_id = decoded
                query = query.where(
                    or_(
                        UserCard.favorite_marked_at < cursor_dt,
                        and_(
                            UserCard.favorite_marked_at == cursor_dt,
                            UserCard.id < cursor_id,
                        ),
                    )
                )

        rows = (await self._session.execute(query)).all()
        has_more = len(rows) > limit
        visible_rows = rows[:limit]
        card_ids = [card.id for card, _film, _game in visible_rows]

        tags_by_card = await self._load_tags(card_ids)
        cat_names = await self._load_category_names(
            list({int(c.category_id) for c, _, _ in visible_rows})
        )
        items = _rows_to_items(visible_rows, tags_by_card, cat_names)

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
        return UserCardListPage(items=items, next_cursor=next_cursor)

    async def _load_tags(self, card_ids: list[int]) -> dict[int, list[str]]:
        tags_by_card: dict[int, list[str]] = {}
        if not card_ids:
            return tags_by_card
        tags_rows = (
            await self._session.execute(
                select(CardTag.card_id, CardTag.tag)
                .where(CardTag.card_id.in_(card_ids))
                .order_by(CardTag.card_id, CardTag.tag)
            )
        ).all()
        for cid, tag in tags_rows:
            tags_by_card.setdefault(cid, []).append(tag)
        return tags_by_card

    async def _load_category_names(self, category_ids: list[int]) -> dict[int, str]:
        names: dict[int, str] = {}
        if not category_ids:
            return names
        cat_rows = (
            await self._session.execute(
                select(UserCardCategory.id, UserCardCategory.name).where(
                    UserCardCategory.id.in_(category_ids)
                )
            )
        ).all()
        for cid, name in cat_rows:
            names[int(cid)] = str(name)
        return names

    async def list_all_for_user(self, user_id: UUID) -> list[UserCardListItem]:
        query: Select[tuple[UserCard, Film | None, Game | None]] = (
            select(UserCard, Film, Game)
            .select_from(UserCard)
            .outerjoin(CatalogItem, CatalogItem.id == UserCard.catalog_item_id)
            .outerjoin(Film, Film.id == func.coalesce(UserCard.film_id, CatalogItem.film_id))
            .outerjoin(Game, Game.id == CatalogItem.game_id)
            .where(UserCard.user_id == user_id)
            .order_by(desc(UserCard.id))
        )
        rows = (await self._session.execute(query)).all()
        card_ids = [card.id for card, _film, _game in rows]

        tags_by_card = await self._load_tags(card_ids)
        cat_names = await self._load_category_names(list({int(c.category_id) for c, _, _ in rows}))
        return _rows_to_items(rows, tags_by_card, cat_names)
