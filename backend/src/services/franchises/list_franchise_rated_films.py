from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.user_card import UserCard
from services.catalog.get_catalog_community_stats import GetCatalogCommunityStatsService
from services.directors.get_director_summary import _rated_card_filters
from services.directors.list_director_rated_films import (
    DirectorFilmItemDTO,
    DirectorFilmsPageDTO,
    _decode_cursor,
    _encode_cursor,
)


@dataclass
class ListFranchiseRatedFilmsService:
    """Lists franchise films that have at least one community rating."""

    _session: AsyncSession
    _community_stats: GetCatalogCommunityStatsService

    class InvalidCursor(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(
            _session=session,
            _community_stats=GetCatalogCommunityStatsService.build(session),
        )

    async def execute(
        self,
        franchise_key: str,
        cursor: str | None,
        limit: int,
        *,
        viewer_user_id: UUID | None = None,
    ) -> DirectorFilmsPageDTO:
        key = franchise_key.strip()
        ratings_subq = (
            select(
                UserCard.film_id.label('film_id'),
                func.count(UserCard.id).label('ratings_count'),
            )
            .where(*_rated_card_filters())
            .group_by(UserCard.film_id)
            .subquery()
        )

        query = (
            select(
                Film,
                ratings_subq.c.ratings_count,
            )
            .join(ratings_subq, ratings_subq.c.film_id == Film.id)
            .where(Film.franchise_key == key)
        )

        if cursor is not None and cursor != '':
            decoded = _decode_cursor(cursor)
            if decoded is None:
                raise self.InvalidCursor
            cursor_count, cursor_film_id = decoded
            query = query.where(
                (ratings_subq.c.ratings_count < cursor_count)
                | ((ratings_subq.c.ratings_count == cursor_count) & (Film.id < cursor_film_id)),
            )

        query = query.order_by(
            desc(ratings_subq.c.ratings_count),
            desc(Film.year),
            desc(Film.id),
        ).limit(limit + 1)

        rows = (await self._session.execute(query)).all()
        has_more = len(rows) > limit
        visible = rows[:limit]

        my_card_by_film: dict[int, int] = {}
        if viewer_user_id is not None and visible:
            film_ids = [int(film.id) for film, _ in visible]
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
        for film, _ratings_count_raw in visible:
            film_id = int(film.id)
            stats = await self._community_stats.execute_for_film_id(film_id)
            items.append(
                DirectorFilmItemDTO(
                    film_id=film_id,
                    title=str(film.title),
                    year=film.year,
                    poster_url=film.poster_url,
                    genres=list(film.genres or []),
                    community_avg_rating=stats.avg_rating,
                    ratings_count=stats.ratings_count,
                    my_card_id=my_card_by_film.get(film_id),
                ),
            )

        next_cursor: str | None = None
        if has_more and visible:
            last_film, last_count = visible[-1]
            next_cursor = _encode_cursor(int(last_count), int(last_film.id))

        return DirectorFilmsPageDTO(items=items, next_cursor=next_cursor)
