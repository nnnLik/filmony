from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.catalog.schemas import (
    CatalogResolveRequest,
    CatalogResolveResponse,
    CatalogSearchHitResponse,
    CatalogSearchProvider,
    CatalogSearchResponse,
)
from api.films.schemas import FilmResponse
from core.database import get_db
from deps.auth import CurrentUser
from providers.kinopoisk.kinopoisk_provider_transport import KinopoiskProviderTransport
from providers.rawg.rawg_provider_transport import RawgProviderTransport
from services.cards.get_my_movie_card_id_for_film import GetMyMovieCardIdForFilmService
from services.catalog.catalog_search_query_normalize import normalize_catalog_search_query
from services.catalog.rawg_catalog_search_hit_dto import RawgCatalogSearchHitDTO
from services.catalog.resolve_catalog_item_service import ResolveCatalogItemService
from services.catalog.search_kinopoisk_films_local_first import (
    CatalogFilmSearchHitDTO,
    SearchKinopoiskFilmsLocalFirstService,
)
from services.catalog.search_rawg_catalog_games_service import SearchRawgCatalogGamesService
from services.kinopoisk.resolve_kinopoisk_film import (
    KinopoiskClientError,
    KinopoiskUrlParseError,
)

router = APIRouter(prefix='/catalog', tags=['catalog'])
logger = logging.getLogger(__name__)


def _film_search_hit(hit: CatalogFilmSearchHitDTO) -> CatalogSearchHitResponse:
    return CatalogSearchHitResponse(
        provider=hit.provider,
        external_id=hit.external_id,
        kind='film',
        title=hit.title,
        subtitle=hit.subtitle,
        cover_url=hit.cover_url,
        catalog_item_id=hit.catalog_item_id,
        source='remote' if hit.source == 'provider' else 'local',
    )


def _game_search_hit(hit: RawgCatalogSearchHitDTO) -> CatalogSearchHitResponse:
    return CatalogSearchHitResponse(
        provider=hit.provider,
        external_id=hit.external_id,
        kind='game',
        title=hit.title,
        subtitle=hit.subtitle,
        cover_url=hit.cover,
        catalog_item_id=hit.catalog_item_id,
        source=hit.source,
    )


@router.get('/search', response_model=CatalogSearchResponse, summary='Поиск в каталоге (Kinopoisk / RAWG)')
async def search_catalog(
    *,
    provider: Annotated[CatalogSearchProvider, Query()],
    db: Annotated[AsyncSession, Depends(get_db)],
    _viewer: CurrentUser,
    q: Annotated[
        str,
        Query(
            min_length=1,
            alias='q',
            description='Поисковая строка: после нормализации (trim, пробелы, lower) ≥ 3 для kinopoisk, ≥ 4 для rawg',
        ),
    ],
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=40)] = 15,
) -> CatalogSearchResponse:
    keyword = normalize_catalog_search_query(q)
    if provider == CatalogSearchProvider.kinopoisk:
        if len(keyword) < 3:
            raise HTTPException(
                status_code=422,
                detail='Query must contain at least 3 non-whitespace characters',
            )
        try:
            result = await SearchKinopoiskFilmsLocalFirstService.build(db).execute(keyword=keyword, page=page)
        except KinopoiskProviderTransport.KinopoiskProviderTransportError as e:
            raise HTTPException(status_code=502, detail=str(e)) from e

        sliced = tuple(result.hits[:limit])
        has_more = result.has_more or len(result.hits) > limit
        return CatalogSearchResponse(items=[_film_search_hit(hit) for hit in sliced], has_more=has_more)

    if len(keyword) < 4:
        raise HTTPException(
            status_code=422,
            detail='Query must contain at least 4 non-whitespace characters for RAWG search',
        )

    try:
        raw_result = await SearchRawgCatalogGamesService.build(db).execute(keyword, limit, page=page)
    except RawgProviderTransport.RawgProviderTransportError as e:
        logger.error(
            'RAWG catalog search failed',
            exc_info=True,
            extra={'catalog_provider': 'rawg', 'error_message': str(e)},
        )
        detail = str(e).strip() or 'RAWG catalog search failed'
        raise HTTPException(status_code=502, detail=detail) from e

    return CatalogSearchResponse(
        items=[_game_search_hit(h) for h in raw_result.hits],
        has_more=raw_result.has_more,
    )


@router.post('/resolve', response_model=CatalogResolveResponse, summary='Резолв элемента каталога по URL провайдера')
async def resolve_catalog_item(
    body: CatalogResolveRequest,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CatalogResolveResponse:
    try:
        catalog_item, film = await ResolveCatalogItemService.build(db).execute(
            provider=body.provider,
            url=body.url,
        )
    except ResolveCatalogItemService.UnsupportedCatalogProviderError as e:
        raise HTTPException(status_code=422, detail='unsupported catalog provider') from e
    except KinopoiskUrlParseError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except KinopoiskClientError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    my_card_id = await GetMyMovieCardIdForFilmService.build(db).execute(viewer.id, film.id)

    return CatalogResolveResponse(
        catalog_item_id=catalog_item.id,
        provider=catalog_item.provider,
        external_id=catalog_item.external_id,
        title=film.title,
        cover_url=film.poster_url,
        summary=film.short_description,
        film=FilmResponse(
            id=film.id,
            kinopoisk_id=film.kinopoisk_id,
            genres=list(film.genres or []),
            title=film.title,
            year=film.year,
            poster_url=film.poster_url,
            short_description=film.short_description,
            description=film.description,
            my_card_id=my_card_id,
        ),
    )
