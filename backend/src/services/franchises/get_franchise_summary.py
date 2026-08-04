from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.user_card import UserCard
from services.directors.get_director_summary import _rated_card_filters
from services.franchises.franchise_label import (
    franchise_fallback_label,
    parse_franchise_min_kinopoisk_id,
)


@dataclass(frozen=True, slots=True)
class FranchiseSummaryDTO:
    franchise_key: str
    label: str
    films_count: int
    avg_community_rating: float | None


@dataclass
class GetFranchiseSummaryService:
    """Returns catalog-wide summary for a franchise cluster with rated films in Filmony."""

    _session: AsyncSession

    class FranchiseNotFound(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, franchise_key: str) -> FranchiseSummaryDTO:
        key = franchise_key.strip()
        if key == '':
            raise self.FranchiseNotFound

        label = await self._resolve_label(key)

        stats_row = (
            await self._session.execute(
                select(
                    func.count(func.distinct(Film.id)),
                    func.avg(UserCard.rating),
                )
                .select_from(Film)
                .join(UserCard, UserCard.film_id == Film.id)
                .where(
                    Film.franchise_key == key,
                    *_rated_card_filters(),
                ),
            )
        ).one()
        films_count = int(stats_row[0] or 0)
        if films_count == 0:
            raise self.FranchiseNotFound

        avg_raw = stats_row[1]
        avg_community_rating = round(float(avg_raw), 1) if avg_raw is not None else None

        return FranchiseSummaryDTO(
            franchise_key=key,
            label=label,
            films_count=films_count,
            avg_community_rating=avg_community_rating,
        )

    async def _resolve_label(self, franchise_key: str) -> str:
        min_kp_id = parse_franchise_min_kinopoisk_id(franchise_key)
        if min_kp_id is not None:
            title_row = (
                await self._session.execute(
                    select(Film.title).where(Film.kinopoisk_id == min_kp_id).limit(1),
                )
            ).scalar_one_or_none()
            if title_row is not None and str(title_row).strip() != '':
                return str(title_row).strip()
        return franchise_fallback_label(franchise_key)
