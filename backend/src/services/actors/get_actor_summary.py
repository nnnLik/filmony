from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.film_actor import FilmActor
from models.person import Person
from models.user_card import UserCard
from services.directors.get_director_summary import _rated_card_filters


@dataclass(frozen=True, slots=True)
class ActorSummaryDTO:
    kinopoisk_id: int
    name: str
    poster_url: str | None
    films_count: int


@dataclass
class GetActorSummaryService:
    """Returns user-scoped summary for a Kinopoisk actor from rated film cast."""

    _session: AsyncSession

    class ActorNotFound(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, kinopoisk_id: int, *, user_id: UUID) -> ActorSummaryDTO:
        person = (
            await self._session.execute(
                select(Person).where(Person.kinopoisk_id == kinopoisk_id),
            )
        ).scalar_one_or_none()
        if person is None:
            raise self.ActorNotFound

        films_count = int(
            (
                await self._session.execute(
                    select(func.count(func.distinct(UserCard.film_id)))
                    .select_from(UserCard)
                    .join(Film, Film.id == UserCard.film_id)
                    .join(FilmActor, FilmActor.film_id == Film.id)
                    .where(
                        UserCard.user_id == user_id,
                        *_rated_card_filters(),
                        FilmActor.person_id == person.id,
                    ),
                )
            ).scalar_one()
            or 0,
        )
        if films_count == 0:
            raise self.ActorNotFound

        return ActorSummaryDTO(
            kinopoisk_id=int(person.kinopoisk_id),
            name=str(person.name),
            poster_url=person.poster_url,
            films_count=films_count,
        )
