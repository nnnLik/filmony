from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from enum import StrEnum
from typing import Self
from uuid import UUID

from sqlalchemy import cast, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.types import Numeric

from models.film import Film
from models.user_card import UserCard
from services.directors.get_director_summary import _rated_card_filters
from services.directors.list_director_rated_films import (
    DirectorFilmItemDTO,
    DirectorFilmsPageDTO,
)
from services.directors.list_director_rated_films import (
    _decode_cursor as _decode_popularity_cursor,
)
from services.directors.list_director_rated_films import (
    _encode_cursor as _encode_popularity_cursor,
)


class CatalogFilmsSort(StrEnum):
    popularity = 'popularity'
    avg_rating = 'avg_rating'


class CatalogFilmsPeriod(StrEnum):
    all_time = 'all_time'
    month = 'month'


_MIN_RATINGS_FOR_AVG_SORT = 3


def _encode_avg_rating_cursor(avg_rating: float, film_id: int) -> str:
    return f'{avg_rating:.1f}:{film_id}'


def _decode_avg_rating_cursor(cursor: str) -> tuple[float, int] | None:
    parts = cursor.split(':', 1)
    if len(parts) != 2:
        return None
    try:
        avg_rating = float(parts[0])
        film_id = int(parts[1], 10)
    except ValueError:
        return None
    if film_id < 1:
        return None
    return avg_rating, film_id


def _period_card_filters(period: CatalogFilmsPeriod) -> tuple[object, ...]:
    filters: list[object] = list(_rated_card_filters())
    if period == CatalogFilmsPeriod.month:
        since = (dt.datetime.now(dt.UTC) - dt.timedelta(days=30)).replace(tzinfo=None)
        filters.append(UserCard.created_at >= since)
    return tuple(filters)


@dataclass
class ListCatalogFilmsService:
    """Lists community-rated films for catalog browse with sort, period, and title filter."""

    _session: AsyncSession

    class InvalidCursor(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        cursor: str | None,
        limit: int,
        *,
        sort: CatalogFilmsSort = CatalogFilmsSort.popularity,
        period: CatalogFilmsPeriod = CatalogFilmsPeriod.all_time,
        q: str | None = None,
        viewer_user_id: UUID | None = None,
    ) -> DirectorFilmsPageDTO:
        card_filters = _period_card_filters(period)
        avg_expr = func.round(cast(func.avg(UserCard.rating), Numeric), 1)

        ratings_subq = (
            select(
                UserCard.film_id.label('film_id'),
                func.count(UserCard.id).label('ratings_count'),
                avg_expr.label('community_avg_rating'),
            )
            .where(*card_filters)
            .group_by(UserCard.film_id)
            .subquery()
        )

        query = select(
            Film,
            ratings_subq.c.ratings_count,
            ratings_subq.c.community_avg_rating,
        ).join(ratings_subq, ratings_subq.c.film_id == Film.id)

        if sort == CatalogFilmsSort.avg_rating:
            query = query.where(ratings_subq.c.ratings_count >= _MIN_RATINGS_FOR_AVG_SORT)

        title_q = (q or '').strip()
        if title_q:
            query = query.where(Film.title.ilike(f'%{title_q}%'))

        if cursor is not None and cursor != '':
            if sort == CatalogFilmsSort.popularity:
                decoded = _decode_popularity_cursor(cursor)
                if decoded is None:
                    raise self.InvalidCursor
                cursor_count, cursor_film_id = decoded
                query = query.where(
                    (ratings_subq.c.ratings_count < cursor_count)
                    | ((ratings_subq.c.ratings_count == cursor_count) & (Film.id < cursor_film_id)),
                )
            else:
                decoded_avg = _decode_avg_rating_cursor(cursor)
                if decoded_avg is None:
                    raise self.InvalidCursor
                cursor_avg, cursor_film_id = decoded_avg
                query = query.where(
                    (ratings_subq.c.community_avg_rating < cursor_avg)
                    | (
                        (ratings_subq.c.community_avg_rating == cursor_avg)
                        & (Film.id < cursor_film_id)
                    ),
                )

        if sort == CatalogFilmsSort.popularity:
            query = query.order_by(
                desc(ratings_subq.c.ratings_count),
                desc(Film.year),
                desc(Film.id),
            )
        else:
            query = query.order_by(
                desc(ratings_subq.c.community_avg_rating),
                desc(Film.year),
                desc(Film.id),
            )

        query = query.limit(limit + 1)

        rows = (await self._session.execute(query)).all()
        has_more = len(rows) > limit
        visible = rows[:limit]

        my_card_by_film: dict[int, int] = {}
        if viewer_user_id is not None and visible:
            film_ids = [int(film.id) for film, _, _ in visible]
            my_rows = (
                await self._session.execute(
                    select(UserCard.film_id, UserCard.id).where(
                        UserCard.user_id == viewer_user_id,
                        UserCard.film_id.in_(film_ids),
                        UserCard.is_planned.is_(False),
                        UserCard.rating >= 1,
                    ),
                )
            ).all()
            my_card_by_film = {int(film_id): int(card_id) for film_id, card_id in my_rows}

        items: list[DirectorFilmItemDTO] = []
        for film, ratings_count_raw, avg_raw in visible:
            film_id = int(film.id)
            ratings_count = int(ratings_count_raw or 0)
            community_avg_rating = (
                round(float(avg_raw), 1) if avg_raw is not None and ratings_count > 0 else None
            )
            items.append(
                DirectorFilmItemDTO(
                    film_id=film_id,
                    title=str(film.title),
                    year=film.year,
                    poster_url=film.poster_url,
                    genres=list(film.genres or []),
                    community_avg_rating=community_avg_rating,
                    ratings_count=ratings_count,
                    my_card_id=my_card_by_film.get(film_id),
                ),
            )

        next_cursor: str | None = None
        if has_more and visible:
            last_film, last_count, last_avg = visible[-1]
            if sort == CatalogFilmsSort.popularity:
                next_cursor = _encode_popularity_cursor(int(last_count), int(last_film.id))
            else:
                avg_for_cursor = round(float(last_avg), 1) if last_avg is not None else 0.0
                next_cursor = _encode_avg_rating_cursor(avg_for_cursor, int(last_film.id))

        return DirectorFilmsPageDTO(items=items, next_cursor=next_cursor)
