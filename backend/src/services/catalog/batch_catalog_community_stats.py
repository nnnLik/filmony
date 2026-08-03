from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Self

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.catalog_item import CatalogItem
from models.user_card import UserCard
from services.catalog.community_stats_dto import CommunityStatsDTO
from services.catalog.get_catalog_community_stats import _rated_card_filters


@dataclass
class BatchCatalogCommunityStatsService:
    """Loads community rating aggregates for many catalog items in one round trip."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, catalog_item_ids: list[int]) -> dict[int, CommunityStatsDTO]:
        unique_ids = list(dict.fromkeys(catalog_item_ids))
        if not unique_ids:
            return {}

        catalog_rows = (
            await self._session.execute(
                select(CatalogItem.id, CatalogItem.film_id).where(
                    CatalogItem.id.in_(unique_ids),
                ),
            )
        ).all()
        film_by_catalog: dict[int, int | None] = {
            int(catalog_id): int(film_id) if film_id is not None else None
            for catalog_id, film_id in catalog_rows
        }
        film_ids = {film_id for film_id in film_by_catalog.values() if film_id is not None}
        catalog_ids_by_film: dict[int, list[int]] = defaultdict(list)
        for catalog_id, film_id in film_by_catalog.items():
            if film_id is not None:
                catalog_ids_by_film[film_id].append(catalog_id)

        match_parts: list[object] = [UserCard.catalog_item_id.in_(unique_ids)]
        if film_ids:
            match_parts.append(UserCard.film_id.in_(film_ids))

        rating_rows = (
            await self._session.execute(
                select(UserCard.catalog_item_id, UserCard.film_id, UserCard.rating).where(
                    *_rated_card_filters(),
                    or_(*match_parts),
                ),
            )
        ).all()

        ratings_by_catalog: dict[int, list[float]] = {catalog_id: [] for catalog_id in unique_ids}
        for card_catalog_id, card_film_id, rating in rating_rows:
            rating_value = float(rating)
            matched: set[int] = set()
            if card_catalog_id is not None and card_catalog_id in ratings_by_catalog:
                matched.add(int(card_catalog_id))
            if card_film_id is not None:
                for catalog_id in catalog_ids_by_film.get(int(card_film_id), []):
                    matched.add(catalog_id)
            for catalog_id in matched:
                ratings_by_catalog[catalog_id].append(rating_value)

        out: dict[int, CommunityStatsDTO] = {}
        for catalog_id in unique_ids:
            ratings = ratings_by_catalog.get(catalog_id, [])
            if not ratings:
                out[catalog_id] = CommunityStatsDTO(avg_rating=None, ratings_count=0)
            else:
                out[catalog_id] = CommunityStatsDTO(
                    avg_rating=round(sum(ratings) / len(ratings), 1),
                    ratings_count=len(ratings),
                )
        return out
