from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from models.game import Game
from models.user_card import UserCard
from services.watchlist.create_watchlist_entry import (
    CreateWatchlistEntryResult,
    CreateWatchlistEntryService,
)
from services.watchlist.watchlist_card_id import watchlist_card_id_for_provider


@dataclass(frozen=True, slots=True)
class CreateWatchlistEntryFromCatalogResult:
    entry: CreateWatchlistEntryResult
    catalog_item: CatalogItem
    film: Film | None
    game: Game | None


@dataclass
class CreateWatchlistEntryFromCatalogService:
    """Creates a watchlist entry from a catalog_item id (Kinopoisk film or RAWG game)."""

    _session: AsyncSession
    _create_service: CreateWatchlistEntryService

    class CatalogItemNotFoundError(Exception):
        pass

    class MovieAlreadyRatedForCatalogError(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(
            _session=session,
            _create_service=CreateWatchlistEntryService.build(session),
        )

    async def execute(
        self,
        *,
        actor_user_id: UUID,
        catalog_item_id: int,
        watch_tag: str = 'watch_later',
        watch_with_user_id: UUID | None = None,
        created_at: dt.datetime,
    ) -> CreateWatchlistEntryFromCatalogResult:
        ci = (
            await self._session.execute(
                select(CatalogItem).where(CatalogItem.id == catalog_item_id)
            )
        ).scalar_one_or_none()
        if ci is None:
            raise self.CatalogItemNotFoundError

        has_card = (
            await self._session.execute(
                select(func.count(UserCard.id)).where(
                    UserCard.user_id == actor_user_id,
                    UserCard.catalog_item_id == catalog_item_id,
                )
            )
        ).scalar_one()
        if int(has_card or 0) > 0:
            raise self.MovieAlreadyRatedForCatalogError

        film: Film | None = None
        game: Game | None = None
        if ci.film_id is not None:
            film = await self._session.get(Film, ci.film_id)
        if ci.game_id is not None:
            game = await self._session.get(Game, ci.game_id)

        card_id = watchlist_card_id_for_provider(ci.provider, ci.external_id)
        data: dict = {'catalog_item_id': int(ci.id)}
        if ci.provider == CatalogProvider.kinopoisk:
            data['kp_id'] = int(ci.external_id)
            if film is not None:
                data['title'] = film.title
        elif ci.provider == CatalogProvider.rawg:
            data['slug'] = ci.external_id
            if game is not None:
                data['title'] = game.name
                data['poster_url'] = game.background_image

        provider_meta = {'provider': ci.provider.value, 'data': data}
        entry = await self._create_service.execute(
            actor_user_id=actor_user_id,
            card_id=card_id,
            provider_meta=provider_meta,
            watch_tag=watch_tag,
            watch_with_user_id=watch_with_user_id,
            created_at=created_at,
        )
        return CreateWatchlistEntryFromCatalogResult(
            entry=entry,
            catalog_item=ci,
            film=film,
            game=game,
        )
