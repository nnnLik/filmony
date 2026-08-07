from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.collection import Collection
from models.collection_film import CollectionFilm
from models.film import Film
from models.film_award_badge import FilmAwardBadgeKind
from models.user_card import UserCard
from services.collections.meaningful_rated_card import meaningful_rated_card_criteria
from services.film_award_badges.list_film_award_badges import (
    FilmAwardBadgeDTO,
    ListFilmAwardBadgesService,
)


@dataclass(frozen=True, slots=True)
class CollectionFilmBadgeDTO:
    kind: FilmAwardBadgeKind
    ceremony_year: int


@dataclass(frozen=True, slots=True)
class CollectionFilmItemDTO:
    film_id: int
    title: str
    year: int | None
    poster_url: str | None
    viewer_has_rated: bool | None
    viewer_card_id: int | None
    award_badges: list[CollectionFilmBadgeDTO]


@dataclass(frozen=True, slots=True)
class CollectionFilmsPageDTO:
    items: list[CollectionFilmItemDTO]
    next_cursor: str | None
    total_count: int


def _encode_cursor(sort_order: int, film_id: int) -> str:
    return f'{sort_order}:{film_id}'


def _decode_cursor(cursor: str) -> tuple[int, int] | None:
    parts = cursor.split(':', 1)
    if len(parts) != 2:
        return None
    try:
        sort_order = int(parts[0], 10)
        film_id = int(parts[1], 10)
    except ValueError:
        return None
    if sort_order < 0 or film_id < 1:
        return None
    return sort_order, film_id


@dataclass
class ListCollectionFilmsService:
    """Paginates collection films by sort_order with optional viewer rated flags."""

    _session: AsyncSession

    class InvalidCursor(Exception):
        pass

    class CollectionNotFound(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        slug: str,
        cursor: str | None,
        limit: int,
        *,
        viewer_user_id: UUID | None = None,
    ) -> CollectionFilmsPageDTO:
        collection = (
            await self._session.execute(
                select(Collection).where(
                    Collection.slug == slug,
                    Collection.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        if collection is None:
            raise self.CollectionNotFound

        collection_id = int(collection.id)
        total_count = int(
            (
                await self._session.execute(
                    select(func.count())
                    .select_from(CollectionFilm)
                    .where(CollectionFilm.collection_id == collection_id)
                )
            ).scalar_one()
        )

        query = (
            select(CollectionFilm, Film)
            .join(Film, Film.id == CollectionFilm.film_id)
            .where(CollectionFilm.collection_id == collection_id)
        )

        if cursor is not None and cursor != '':
            decoded = _decode_cursor(cursor)
            if decoded is None:
                raise self.InvalidCursor
            cursor_sort, cursor_film_id = decoded
            query = query.where(
                (CollectionFilm.sort_order > cursor_sort)
                | (
                    (CollectionFilm.sort_order == cursor_sort)
                    & (CollectionFilm.film_id > cursor_film_id)
                ),
            )

        query = query.order_by(
            CollectionFilm.sort_order.asc(),
            CollectionFilm.film_id.asc(),
        ).limit(limit + 1)

        rows = (await self._session.execute(query)).all()
        has_more = len(rows) > limit
        visible = rows[:limit]

        rated_film_ids: set[int] = set()
        card_by_film: dict[int, int] = {}
        if viewer_user_id is not None and visible:
            film_ids = [int(film.id) for _, film in visible]
            rated_rows = (
                await self._session.execute(
                    select(UserCard.film_id, UserCard.id).where(
                        UserCard.film_id.in_(film_ids),
                        *meaningful_rated_card_criteria(user_id=viewer_user_id),
                    )
                )
            ).all()
            for film_id, card_id in rated_rows:
                fid = int(film_id)
                rated_film_ids.add(fid)
                card_by_film[fid] = int(card_id)

        badge_rows_by_film: dict[int, list[FilmAwardBadgeDTO]] = {}
        if visible:
            film_ids = [int(film.id) for _, film in visible]
            badge_rows_by_film = await ListFilmAwardBadgesService.build(
                self._session,
            ).execute_many(film_ids)

        items: list[CollectionFilmItemDTO] = []
        for _cf, film in visible:
            film_id = int(film.id)
            viewer_has_rated: bool | None = None
            viewer_card_id: int | None = None
            if viewer_user_id is not None:
                viewer_has_rated = film_id in rated_film_ids
                viewer_card_id = card_by_film.get(film_id)
            award_badges = [
                CollectionFilmBadgeDTO(kind=row.kind, ceremony_year=row.ceremony_year)
                for row in badge_rows_by_film.get(film_id, [])
            ]
            items.append(
                CollectionFilmItemDTO(
                    film_id=film_id,
                    title=str(film.title),
                    year=film.year,
                    poster_url=film.poster_url,
                    viewer_has_rated=viewer_has_rated,
                    viewer_card_id=viewer_card_id,
                    award_badges=award_badges,
                ),
            )

        next_cursor: str | None = None
        if has_more and visible:
            last_cf, last_film = visible[-1]
            next_cursor = _encode_cursor(int(last_cf.sort_order), int(last_film.id))

        return CollectionFilmsPageDTO(
            items=items,
            next_cursor=next_cursor,
            total_count=total_count,
        )
