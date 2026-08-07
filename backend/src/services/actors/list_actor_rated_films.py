from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.film_actor import FilmActor
from models.person import Person
from models.user_card import UserCard
from services.directors.get_director_summary import _rated_card_filters


@dataclass(frozen=True, slots=True)
class ActorFilmItemDTO:
    film_id: int
    title: str
    year: int | None
    poster_url: str | None
    genres: list[str]
    role: str | None
    my_card_id: int | None
    rating: float | None
    rated_at: dt.datetime | None


@dataclass(frozen=True, slots=True)
class ActorFilmsPageDTO:
    items: list[ActorFilmItemDTO]
    next_cursor: str | None


def _completion_timestamp():
    return func.coalesce(UserCard.completed_at, UserCard.created_at)


def _encode_cursor(rated_at: dt.datetime, film_id: int) -> str:
    return f'{rated_at.isoformat()}:{film_id}'


def _decode_cursor(cursor: str) -> tuple[dt.datetime, int] | None:
    parts = cursor.rsplit(':', 1)
    if len(parts) != 2:
        return None
    try:
        rated_at = dt.datetime.fromisoformat(parts[0])
        film_id = int(parts[1], 10)
    except ValueError:
        return None
    if film_id < 1:
        return None
    return rated_at, film_id


@dataclass
class ListActorRatedFilmsService:
    """Lists rated films for a user where the actor appears in stored cast."""

    _session: AsyncSession

    class InvalidCursor(Exception):
        pass

    class ActorNotFound(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        kinopoisk_id: int,
        cursor: str | None,
        limit: int,
        *,
        user_id: UUID,
        viewer_user_id: UUID | None = None,
    ) -> ActorFilmsPageDTO:
        person = (
            await self._session.execute(
                select(Person).where(Person.kinopoisk_id == kinopoisk_id),
            )
        ).scalar_one_or_none()
        if person is None:
            raise self.ActorNotFound

        completion = _completion_timestamp()
        query = (
            select(
                Film,
                FilmActor.role,
                UserCard.id,
                UserCard.rating,
                completion.label('rated_at'),
            )
            .select_from(UserCard)
            .join(Film, Film.id == UserCard.film_id)
            .join(FilmActor, FilmActor.film_id == Film.id)
            .where(
                UserCard.user_id == user_id,
                *_rated_card_filters(),
                FilmActor.person_id == person.id,
            )
        )

        if cursor is not None and cursor != '':
            decoded = _decode_cursor(cursor)
            if decoded is None:
                raise self.InvalidCursor
            cursor_rated_at, cursor_film_id = decoded
            query = query.where(
                (completion < cursor_rated_at)
                | ((completion == cursor_rated_at) & (Film.id < cursor_film_id)),
            )

        query = query.order_by(desc(completion), desc(Film.id)).limit(limit + 1)
        rows = (await self._session.execute(query)).all()
        has_more = len(rows) > limit
        visible = rows[:limit]

        my_card_by_film: dict[int, int] = {}
        if viewer_user_id is not None and visible and viewer_user_id != user_id:
            film_ids = [int(film.id) for film, _, _, _, _ in visible]
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

        items: list[ActorFilmItemDTO] = []
        for film, role, card_id, rating, rated_at in visible:
            film_id = int(film.id)
            viewer_card_id = (
                int(card_id) if viewer_user_id == user_id else my_card_by_film.get(film_id)
            )
            items.append(
                ActorFilmItemDTO(
                    film_id=film_id,
                    title=str(film.title),
                    year=film.year,
                    poster_url=film.poster_url,
                    genres=list(film.genres or []),
                    role=str(role).strip() if role else None,
                    my_card_id=viewer_card_id,
                    rating=float(rating) if rating is not None else None,
                    rated_at=rated_at,
                ),
            )

        next_cursor: str | None = None
        if has_more and visible:
            last_film, _, _, _, last_rated_at = visible[-1]
            if last_rated_at is not None:
                next_cursor = _encode_cursor(last_rated_at, int(last_film.id))

        return ActorFilmsPageDTO(items=items, next_cursor=next_cursor)
