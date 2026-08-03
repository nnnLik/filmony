from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.catalog_item import CatalogItem
from services.catalog.community_card_dto import (
    CommunityAuthorDTO,
    CommunityCardDTO,
    CommunityCardsPageDTO,
)
from services.catalog.list_catalog_community_cards import ListCatalogCommunityCardsService

FilmCommunityAuthorDTO = CommunityAuthorDTO
FilmCommunityCardDTO = CommunityCardDTO
FilmCommunityCardsPageDTO = CommunityCardsPageDTO


@dataclass
class ListFilmCommunityCardsService:
    """Loads public movie cards for a catalog film (who rated it, notes, tags).

    Powers the catalog film page so viewers can read community scores and notes before adding their own card.
    """

    _session: AsyncSession
    _catalog_svc: ListCatalogCommunityCardsService

    class InvalidCursor(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(
            _session=session,
            _catalog_svc=ListCatalogCommunityCardsService.build(session),
        )

    async def execute(
        self, film_id: int, cursor: str | None, limit: int
    ) -> FilmCommunityCardsPageDTO:
        catalog_item_id = (
            await self._session.execute(
                select(CatalogItem.id).where(CatalogItem.film_id == film_id).limit(1)
            )
        ).scalar_one_or_none()

        try:
            if catalog_item_id is not None:
                return await self._catalog_svc.execute(
                    cursor,
                    limit,
                    catalog_item_id=int(catalog_item_id),
                    film_id=film_id,
                )
            return await self._catalog_svc.execute(
                cursor,
                limit,
                film_id=film_id,
            )
        except ListCatalogCommunityCardsService.InvalidCursor as exc:
            raise self.InvalidCursor from exc
