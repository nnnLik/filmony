from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.user_card import UserCard


@dataclass(frozen=True, slots=True)
class RatedDirectorItemDTO:
    kinopoisk_id: int
    name: str
    count: int


@dataclass
class ListUserRatedDirectorsService:
    """Lists directors the user rated, with film counts per director."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, user_id: UUID) -> list[RatedDirectorItemDTO]:
        rows = (
            await self._session.execute(
                select(
                    Film.primary_director_kinopoisk_id,
                    Film.primary_director_name,
                    func.count(UserCard.id).label('count'),
                )
                .join(Film, Film.id == UserCard.film_id)
                .where(
                    UserCard.user_id == user_id,
                    UserCard.is_planned.is_(False),
                    UserCard.rating >= 1,
                    Film.primary_director_kinopoisk_id.is_not(None),
                )
                .group_by(
                    Film.primary_director_kinopoisk_id,
                    Film.primary_director_name,
                )
                .order_by(func.count(UserCard.id).desc(), Film.primary_director_name.asc())
            )
        ).all()

        return [
            RatedDirectorItemDTO(
                kinopoisk_id=int(row.primary_director_kinopoisk_id),
                name=str(row.primary_director_name or ''),
                count=int(row.count),
            )
            for row in rows
        ]
