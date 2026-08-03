from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.catalog_item import CatalogItem
from models.user_card import UserCard
from services.catalog.community_stats_dto import CommunityStatsDTO


def _rated_card_filters():
    return (
        UserCard.is_planned.is_(False),
        UserCard.rating >= 1,
    )


@dataclass
class GetCatalogCommunityStatsService:
    """Aggregates community average rating for a catalog title across linked user cards."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, catalog_item_id: int) -> CommunityStatsDTO:
        film_id = (
            await self._session.execute(
                select(CatalogItem.film_id).where(CatalogItem.id == catalog_item_id),
            )
        ).scalar_one_or_none()
        return await self._aggregate(
            catalog_item_id=catalog_item_id,
            film_id=int(film_id) if film_id is not None else None,
        )

    async def execute_for_film_id(self, film_id: int) -> CommunityStatsDTO:
        return await self._aggregate(catalog_item_id=None, film_id=film_id)

    async def _aggregate(
        self,
        *,
        catalog_item_id: int | None,
        film_id: int | None,
    ) -> CommunityStatsDTO:
        if catalog_item_id is None and film_id is None:
            return CommunityStatsDTO(avg_rating=None, ratings_count=0)

        match_parts: list[object] = []
        if catalog_item_id is not None:
            match_parts.append(UserCard.catalog_item_id == catalog_item_id)
        if film_id is not None:
            match_parts.append(UserCard.film_id == film_id)
        if not match_parts:
            return CommunityStatsDTO(avg_rating=None, ratings_count=0)

        row = (
            await self._session.execute(
                select(
                    func.avg(UserCard.rating),
                    func.count(UserCard.id),
                ).where(
                    *_rated_card_filters(),
                    or_(*match_parts),
                ),
            )
        ).one()
        avg_raw, count_raw = row
        count = int(count_raw or 0)
        if count == 0:
            return CommunityStatsDTO(avg_rating=None, ratings_count=0)
        return CommunityStatsDTO(
            avg_rating=round(float(avg_raw), 1),
            ratings_count=count,
        )
