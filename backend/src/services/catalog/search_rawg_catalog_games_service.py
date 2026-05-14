from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Self

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.catalog_item import CatalogProvider
from models.game import Game
from providers.rawg import RawgGamesListQueryParams, RawgProviderTransport
from services.search.ilike_escape import escape_ilike_pattern

from .ensure_rawg_catalog_item_service import EnsureRawgCatalogItemService
from .rawg_catalog_search_hit_dto import RawgCatalogSearchHitDTO
from .ttl_coalescing_cache import RAWG_GAME_SEARCH_CACHE
from .upsert_rawg_game_from_list_dto_service import UpsertRawgGameFromListDtoService


@dataclass(frozen=True, slots=True)
class SearchRawgCatalogGamesResult:
    """Local-first RAWG search hits plus a conservative ``has_more`` signal."""

    hits: tuple[RawgCatalogSearchHitDTO, ...]
    has_more: bool


@dataclass
class SearchRawgCatalogGamesService:
    """Local-first RAWG-backed game lookup: persisted rows win, RAWG fills the remainder."""

    _session: AsyncSession
    _rawg_transport: RawgProviderTransport

    @classmethod
    def build(cls, session: AsyncSession, transport: RawgProviderTransport | None = None) -> Self:
        return cls(_session=session, _rawg_transport=transport or RawgProviderTransport())

    async def execute(
        self,
        query_text: str,
        limit: int,
        *,
        page: int = 1,
        allow_remote: bool = True,
    ) -> SearchRawgCatalogGamesResult:
        q = query_text.strip()
        if not q:
            return SearchRawgCatalogGamesResult((), False)

        clipped = max(1, min(limit, 40))
        page = max(1, page)
        return await RAWG_GAME_SEARCH_CACHE.get_or_fetch(
            f'rawg:game_search:{q}:{clipped}:{page}:{allow_remote}',
            lambda: self._execute_impl(q, clipped, page, allow_remote),
        )

    async def _execute_impl(
        self,
        q: str,
        clipped: int,
        page: int,
        allow_remote: bool,
    ) -> SearchRawgCatalogGamesResult:
        hits: list[RawgCatalogSearchHitDTO] = []
        merged_ids: set[int] = set()
        upsert_svc = UpsertRawgGameFromListDtoService.build(self._session)
        ensure_svc = EnsureRawgCatalogItemService.build(self._session)

        if page > 1:
            if not allow_remote:
                await self._session.commit()
                return SearchRawgCatalogGamesResult((), False)

            remote_doc = await self._rawg_transport.search_games(
                RawgGamesListQueryParams.for_search(
                    search=q,
                    page=page,
                    page_size=max(clipped, 5),
                )
            )

            for dto in remote_doc.results:
                if dto.id is None or dto.id in merged_ids:
                    continue
                merged_ids.add(dto.id)
                game_row = await upsert_svc.execute(dto)
                ci = await ensure_svc.execute(game=game_row)
                hits.append(self._dto_for_game(ci.id, game_row, source='remote'))
                if len(hits) >= clipped:
                    break

            await self._session.commit()
            return SearchRawgCatalogGamesResult(
                tuple(hits),
                has_more=bool(remote_doc.next_url),
            )

        pattern = f'%{escape_ilike_pattern(q)}%'
        stmt = (
            select(Game)
            .where(
                or_(
                    Game.name.ilike(pattern, escape='\\'),
                    Game.name_original.is_not(None)
                    & Game.name_original.ilike(pattern, escape='\\'),
                    Game.slug.is_not(None) & Game.slug.ilike(pattern, escape='\\'),
                )
            )
            .order_by(Game.name.asc().nulls_last(), Game.rawg_id.asc())
            .limit(clipped)
        )
        local_rows = (await self._session.execute(stmt)).scalars().all()

        for game in local_rows:
            merged_ids.add(game.rawg_id)
            ci = await ensure_svc.execute(game=game)
            hits.append(self._dto_for_game(ci.id, game, source='local'))

        need = clipped - len(hits)
        if need <= 0 or not allow_remote:
            await self._session.commit()
            return SearchRawgCatalogGamesResult(
                tuple(hits),
                has_more=len(local_rows) >= clipped,
            )

        remote_doc = await self._rawg_transport.search_games(
            RawgGamesListQueryParams.for_search(
                search=q,
                page=1,
                page_size=max(need, 5),
            )
        )

        for dto in remote_doc.results:
            if dto.id is None or dto.id in merged_ids:
                continue
            merged_ids.add(dto.id)
            game_row = await upsert_svc.execute(dto)
            ci = await ensure_svc.execute(game=game_row)
            hits.append(self._dto_for_game(ci.id, game_row, source='remote'))
            if len(hits) >= clipped:
                break

        await self._session.commit()
        has_more_remote = bool(remote_doc.next_url)
        return SearchRawgCatalogGamesResult(tuple(hits), has_more=has_more_remote)

    @staticmethod
    def _dto_for_game(
        catalog_item_id: int, game: Game, *, source: Literal['local', 'remote']
    ) -> RawgCatalogSearchHitDTO:
        return RawgCatalogSearchHitDTO(
            provider=CatalogProvider.rawg,
            external_id=str(game.rawg_id),
            kind='game',
            title=game.name or 'Untitled',
            subtitle=game.released,
            cover=game.background_image,
            source=source,
            catalog_item_id=catalog_item_id,
        )


__all__ = ('SearchRawgCatalogGamesResult', 'SearchRawgCatalogGamesService')
