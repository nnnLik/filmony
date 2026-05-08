from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import cast
from uuid import UUID

from sqlalchemy import Select, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.user_watchlist_film import UserWatchlistFilm


@dataclass(frozen=True, slots=True)
class WatchlistFilmListItem:
    film_id: int
    film_kinopoisk_id: int
    film_genres: list[str]
    film_title: str
    film_year: int | None
    film_poster_url: str | None
    created_at: dt.datetime


@dataclass(frozen=True, slots=True)
class WatchlistFilmPage:
    items: list[WatchlistFilmListItem]
    next_cursor: str | None


class ListUserWatchlistFilmsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        user_id: UUID,
        cursor: str | None,
        limit: int,
    ) -> WatchlistFilmPage:
        query: Select[tuple[UserWatchlistFilm, Film]] = (
            select(UserWatchlistFilm, Film)
            .join(Film, Film.id == UserWatchlistFilm.film_id)
            .where(UserWatchlistFilm.user_id == user_id)
            .order_by(desc(UserWatchlistFilm.id))
            .limit(limit + 1)
        )
        if cursor is not None and cursor != '':
            query = query.where(UserWatchlistFilm.id < int(cursor))

        rows = (await self._session.execute(query)).all()
        has_more = len(rows) > limit
        visible_rows = rows[:limit]
        items = [
            WatchlistFilmListItem(
                film_id=film.id,
                film_kinopoisk_id=film.kinopoisk_id,
                film_genres=list(film.genres or []),
                film_title=film.title,
                film_year=film.year,
                film_poster_url=film.poster_url,
                created_at=w.created_at,
            )
            for w, film in visible_rows
        ]
        next_cursor = str(cast(int, visible_rows[-1][0].id)) if has_more and visible_rows else None
        return WatchlistFilmPage(items=items, next_cursor=next_cursor)
