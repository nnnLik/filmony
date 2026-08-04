from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.user_card import UserCard


def _rated_card_filters():
    return (
        UserCard.is_planned.is_(False),
        UserCard.rating >= 1,
        UserCard.film_id.is_not(None),
    )


@dataclass(frozen=True, slots=True)
class DirectorSummaryDTO:
    kinopoisk_id: int
    name: str
    poster_url: str | None
    films_count: int
    avg_community_rating: float | None


@dataclass
class GetDirectorSummaryService:
    """Returns catalog-wide summary for a Kinopoisk director with rated films in Filmony."""

    _session: AsyncSession

    class DirectorNotFound(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, kinopoisk_id: int) -> DirectorSummaryDTO:
        name_row = (
            await self._session.execute(
                select(Film.primary_director_name)
                .where(Film.primary_director_kinopoisk_id == kinopoisk_id)
                .where(Film.primary_director_name.is_not(None))
                .limit(1),
            )
        ).scalar_one_or_none()
        poster_row = (
            await self._session.execute(
                select(Film.primary_director_poster_url)
                .where(Film.primary_director_kinopoisk_id == kinopoisk_id)
                .where(Film.primary_director_poster_url.is_not(None))
                .limit(1),
            )
        ).scalar_one_or_none()
        if name_row is None:
            has_any = (
                await self._session.execute(
                    select(func.count())
                    .select_from(Film)
                    .where(Film.primary_director_kinopoisk_id == kinopoisk_id),
                )
            ).scalar_one()
            if int(has_any or 0) == 0:
                raise self.DirectorNotFound
        name = str(name_row).strip() if name_row else f'Режиссёр #{kinopoisk_id}'

        stats_row = (
            await self._session.execute(
                select(
                    func.count(func.distinct(Film.id)),
                    func.avg(UserCard.rating),
                )
                .select_from(Film)
                .join(UserCard, UserCard.film_id == Film.id)
                .where(
                    Film.primary_director_kinopoisk_id == kinopoisk_id,
                    *_rated_card_filters(),
                ),
            )
        ).one()
        films_count = int(stats_row[0] or 0)
        if films_count == 0:
            raise self.DirectorNotFound

        avg_raw = stats_row[1]
        avg_community_rating = round(float(avg_raw), 1) if avg_raw is not None else None

        return DirectorSummaryDTO(
            kinopoisk_id=kinopoisk_id,
            name=name,
            poster_url=str(poster_row).strip() if poster_row else None,
            films_count=films_count,
            avg_community_rating=avg_community_rating,
        )
