from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from models.catalog_item import CatalogItem, CatalogProvider
from models.game import Game


@dataclass
class EnsureRawgCatalogItemService:
    """Idempotently attaches ``CatalogItem(provider=rawg, external_id, game_id).``"""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, *, game: Game) -> CatalogItem:
        external_id = str(game.rawg_id)
        stmt = (
            pg_insert(CatalogItem)
            .values(
                provider=CatalogProvider.rawg,
                external_id=external_id,
                film_id=None,
                game_id=game.id,
            )
            .on_conflict_do_update(
                constraint='uq_catalog_item_provider_external',
                set_={'game_id': game.id},
            )
            .returning(CatalogItem.id)
        )
        item_id_any = await self._session.scalar(stmt)
        if item_id_any is None:
            raise RuntimeError('ensure rawg catalog_item: unexpected empty returning')
        item_id = int(item_id_any)

        refreshed = (
            await self._session.execute(select(CatalogItem).where(CatalogItem.id == item_id))
        ).scalar_one()
        return refreshed


__all__ = ('EnsureRawgCatalogItemService',)
