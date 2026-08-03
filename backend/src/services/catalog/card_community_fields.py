from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from services.catalog.batch_catalog_community_stats import BatchCatalogCommunityStatsService
from services.catalog.community_stats_dto import CommunityStatsDTO, is_contrarian
from services.catalog.get_catalog_community_stats import GetCatalogCommunityStatsService


class _CardCommunityLookup(Protocol):
    id: int
    catalog_item_id: int | None
    film_id: int | None
    rating: float


@dataclass(frozen=True, slots=True)
class CardCommunityFields:
    community_avg_rating: float | None
    is_contrarian: bool


_EMPTY_STATS = CommunityStatsDTO(avg_rating=None, ratings_count=0)


async def load_card_community_fields(
    session: AsyncSession,
    *,
    cards: list[_CardCommunityLookup],
    viewer_user_id: UUID,
    owner_user_id: UUID,
) -> dict[int, CardCommunityFields]:
    """Resolve community avg and contrarian flag for profile/card list items."""
    if not cards:
        return {}

    catalog_ids = [int(card.catalog_item_id) for card in cards if card.catalog_item_id is not None]
    batch_stats = await BatchCatalogCommunityStatsService.build(session).execute(catalog_ids)

    film_ids = sorted(
        {
            int(card.film_id)
            for card in cards
            if card.catalog_item_id is None and card.film_id is not None
        },
    )
    film_stats: dict[int, CommunityStatsDTO] = {}
    stats_service = GetCatalogCommunityStatsService.build(session)
    for film_id in film_ids:
        film_stats[film_id] = await stats_service.execute_for_film_id(film_id)

    include_contrarian = viewer_user_id == owner_user_id
    out: dict[int, CardCommunityFields] = {}
    for card in cards:
        stats = _EMPTY_STATS
        if card.catalog_item_id is not None:
            stats = batch_stats.get(int(card.catalog_item_id), _EMPTY_STATS)
        elif card.film_id is not None:
            stats = film_stats.get(int(card.film_id), _EMPTY_STATS)

        contrarian = False
        if include_contrarian:
            contrarian = is_contrarian(
                user_rating=float(card.rating),
                avg_rating=stats.avg_rating,
                ratings_count=stats.ratings_count,
            )
        out[int(card.id)] = CardCommunityFields(
            community_avg_rating=stats.avg_rating,
            is_contrarian=contrarian,
        )
    return out


async def load_single_card_community_fields(
    session: AsyncSession,
    *,
    catalog_item_id: int | None,
    film_id: int | None,
    user_rating: float,
    viewer_user_id: UUID,
    owner_user_id: UUID,
) -> CardCommunityFields:
    stats_service = GetCatalogCommunityStatsService.build(session)
    if catalog_item_id is not None:
        stats = await stats_service.execute(catalog_item_id)
    elif film_id is not None:
        stats = await stats_service.execute_for_film_id(film_id)
    else:
        stats = _EMPTY_STATS

    contrarian = False
    if viewer_user_id == owner_user_id:
        contrarian = is_contrarian(
            user_rating=user_rating,
            avg_rating=stats.avg_rating,
            ratings_count=stats.ratings_count,
        )
    return CardCommunityFields(
        community_avg_rating=stats.avg_rating,
        is_contrarian=contrarian,
    )
