from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.user_card import UserCard
from services.franchises.franchise_label import resolve_franchise_label


@dataclass(frozen=True, slots=True)
class RatedFranchiseItemDTO:
    franchise_key: str
    label: str
    count: int


@dataclass
class ListUserRatedFranchisesService:
    """Lists franchises the user rated, with film counts per franchise."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, user_id: UUID) -> list[RatedFranchiseItemDTO]:
        rows = (
            await self._session.execute(
                select(
                    Film.franchise_key,
                    func.count(UserCard.id).label('count'),
                )
                .join(Film, Film.id == UserCard.film_id)
                .where(
                    UserCard.user_id == user_id,
                    UserCard.is_planned.is_(False),
                    UserCard.rating >= 1,
                    Film.franchise_key.is_not(None),
                )
                .group_by(Film.franchise_key)
                .order_by(func.count(UserCard.id).desc(), Film.franchise_key.asc())
            )
        ).all()

        result: list[RatedFranchiseItemDTO] = []
        for row in rows:
            key = str(row.franchise_key)
            label = await resolve_franchise_label(self._session, key)
            result.append(
                RatedFranchiseItemDTO(
                    franchise_key=key,
                    label=label,
                    count=int(row.count),
                ),
            )
        return result
