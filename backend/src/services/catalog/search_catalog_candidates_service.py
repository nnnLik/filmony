from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.database import get_session_factory
from models.catalog_item import CatalogProvider
from providers.kinopoisk.kinopoisk_provider_transport import KinopoiskProviderTransport
from providers.rawg.rawg_provider_transport import RawgProviderTransport
from services.catalog.catalog_candidate_dto import (
    CatalogCandidateDTO,
    SearchCatalogCandidatesResult,
)
from services.catalog.catalog_search_query_normalize import normalize_catalog_search_query
from services.catalog.rawg_catalog_search_hit_dto import RawgCatalogSearchHitDTO
from services.catalog.search_kinopoisk_films_local_first import (
    CatalogFilmSearchHitDTO,
    SearchKinopoiskFilmsLocalFirstService,
    SearchKinopoiskFilmsResult,
)
from services.catalog.search_rawg_catalog_games_service import (
    SearchRawgCatalogGamesResult,
    SearchRawgCatalogGamesService,
)

logger = logging.getLogger(__name__)

_KINOPOISK_MIN_LEN = 3
_RAWG_MIN_LEN = 4


def _film_hit_to_candidate(hit: CatalogFilmSearchHitDTO) -> CatalogCandidateDTO:
    source = 'remote' if hit.source == 'provider' else 'local'
    return CatalogCandidateDTO(
        provider=hit.provider,
        external_id=hit.external_id,
        kind='film',
        kind_hint='film',
        title=hit.title,
        subtitle=hit.subtitle,
        cover_url=hit.cover_url,
        catalog_item_id=hit.catalog_item_id,
        source=source,
    )


def _game_hit_to_candidate(hit: RawgCatalogSearchHitDTO) -> CatalogCandidateDTO:
    return CatalogCandidateDTO(
        provider=hit.provider,
        external_id=hit.external_id,
        kind='game',
        kind_hint='game',
        title=hit.title,
        subtitle=hit.subtitle,
        cover_url=hit.cover,
        catalog_item_id=hit.catalog_item_id,
        source=hit.source,
    )


def _merge_candidates(
    *,
    film_result: SearchKinopoiskFilmsResult | None,
    game_result: SearchRawgCatalogGamesResult | None,
    limit: int,
) -> tuple[tuple[CatalogCandidateDTO, ...], bool]:
    merged: list[CatalogCandidateDTO] = []
    seen: set[tuple[CatalogProvider, str]] = set()

    for hit in film_result.hits if film_result is not None else ():
        key = (hit.provider, hit.external_id)
        if key in seen:
            continue
        seen.add(key)
        merged.append(_film_hit_to_candidate(hit))

    for hit in game_result.hits if game_result is not None else ():
        key = (hit.provider, hit.external_id)
        if key in seen:
            continue
        seen.add(key)
        merged.append(_game_hit_to_candidate(hit))

    merged.sort(key=lambda c: (0 if c.source == 'local' else 1, c.title.lower()))

    has_more = False
    if film_result is not None and film_result.has_more:
        has_more = True
    if game_result is not None and game_result.has_more:
        has_more = True
    if len(merged) > limit:
        has_more = True

    return tuple(merged[:limit]), has_more


@dataclass
class SearchCatalogCandidatesService:
    """Parallel Kinopoisk + RAWG search merged into one mixed candidate list.

    Returns partial results when one provider fails: surviving hits stay in ``items``
    and the failing provider id is listed in ``degraded_sources``.
    """

    _session_factory: async_sessionmaker[AsyncSession]
    _kinopoisk_transport: KinopoiskProviderTransport
    _rawg_transport: RawgProviderTransport

    @classmethod
    def build(
        cls,
        session: AsyncSession,
        *,
        kinopoisk_transport: KinopoiskProviderTransport | None = None,
        rawg_transport: RawgProviderTransport | None = None,
    ) -> Self:
        _ = session
        return cls(
            _session_factory=get_session_factory(),
            _kinopoisk_transport=kinopoisk_transport or KinopoiskProviderTransport(),
            _rawg_transport=rawg_transport or RawgProviderTransport(),
        )

    async def _fetch_kinopoisk(self, keyword: str, page: int) -> SearchKinopoiskFilmsResult:
        async with self._session_factory() as session:
            return await SearchKinopoiskFilmsLocalFirstService.build(
                session,
                transport=self._kinopoisk_transport,
            ).execute(keyword=keyword, page=page)

    async def _fetch_rawg(
        self,
        keyword: str,
        limit: int,
        page: int,
    ) -> SearchRawgCatalogGamesResult:
        async with self._session_factory() as session:
            return await SearchRawgCatalogGamesService.build(
                session,
                transport=self._rawg_transport,
            ).execute(keyword, limit, page=page)

    async def execute(
        self,
        keyword: str,
        *,
        page: int = 1,
        limit: int = 15,
    ) -> SearchCatalogCandidatesResult:
        norm = normalize_catalog_search_query(keyword)
        if len(norm) < _KINOPOISK_MIN_LEN:
            return SearchCatalogCandidatesResult(items=(), has_more=False, degraded_sources=())

        clipped_limit = max(1, min(limit, 40))
        page = max(1, page)

        tasks: list[asyncio.Task] = []
        source_names: list[str] = []

        if len(norm) >= _KINOPOISK_MIN_LEN:
            source_names.append('kinopoisk')
            tasks.append(asyncio.create_task(self._fetch_kinopoisk(norm, page)))

        if len(norm) >= _RAWG_MIN_LEN:
            source_names.append('rawg')
            tasks.append(asyncio.create_task(self._fetch_rawg(norm, clipped_limit, page)))

        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        film_result: SearchKinopoiskFilmsResult | None = None
        game_result: SearchRawgCatalogGamesResult | None = None
        degraded_sources: list[str] = []

        for name, outcome in zip(source_names, raw_results, strict=True):
            if isinstance(outcome, Exception):
                logger.warning(
                    'Catalog candidate source failed',
                    exc_info=outcome,
                    extra={'catalog_source': name},
                )
                degraded_sources.append(name)
                continue
            if name == 'kinopoisk':
                film_result = outcome
            else:
                game_result = outcome

        items, has_more = _merge_candidates(
            film_result=film_result,
            game_result=game_result,
            limit=clipped_limit,
        )
        return SearchCatalogCandidatesResult(
            items=items,
            has_more=has_more,
            degraded_sources=tuple(degraded_sources),
        )


__all__ = ('SearchCatalogCandidatesService',)
