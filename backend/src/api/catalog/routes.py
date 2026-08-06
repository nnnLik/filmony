from __future__ import annotations

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.cards.schemas import FollowingRatingsListResponse
from api.catalog.schemas import (
    CatalogCandidateResponse,
    CatalogCandidatesMetaResponse,
    CatalogCandidatesResponse,
    CatalogCommunityAuthorResponse,
    CatalogCommunityCardItemResponse,
    CatalogCommunityCardsPageResponse,
    CatalogItemDetailResponse,
    CatalogResolveByUrlRequest,
    CatalogResolveByUrlResponse,
    CatalogResolveRequest,
    CatalogResolveResponse,
    CatalogSearchHitResponse,
    CatalogSearchProvider,
    CatalogSearchResponse,
)
from api.films.award_badges import film_award_badge_responses
from api.films.schemas import FilmResponse
from core.database import get_db
from deps.auth import CurrentUser
from models.catalog_item import CatalogItem, CatalogProvider
from models.user_card import UserCard
from providers.kinopoisk.kinopoisk_provider_transport import KinopoiskProviderTransport
from providers.rawg.rawg_provider_transport import RawgProviderTransport
from services.cards.following_ratings_response import following_ratings_list_response
from services.cards.get_my_user_card_id_for_catalog_item import GetMyUserCardIdForCatalogItemService
from services.cards.get_my_user_card_id_for_linked_film import GetMyUserCardIdForLinkedFilmService
from services.cards.list_following_ratings_for_title import ListFollowingRatingsForTitleService
from services.catalog.catalog_candidate_dto import CatalogCandidateDTO
from services.catalog.catalog_search_query_normalize import normalize_catalog_search_query
from services.catalog.get_catalog_item_detail import GetCatalogItemDetailService
from services.catalog.list_catalog_community_cards import ListCatalogCommunityCardsService
from services.catalog.rawg_catalog_search_hit_dto import RawgCatalogSearchHitDTO
from services.catalog.resolve_catalog_by_url_service import ResolveCatalogByUrlService
from services.catalog.resolve_catalog_item_service import ResolveCatalogItemService
from services.catalog.resolve_youtube_video_by_url_service import ResolveYoutubeVideoByUrlService
from services.catalog.search_catalog_candidates_service import SearchCatalogCandidatesService
from services.catalog.search_kinopoisk_films_local_first import (
    CatalogFilmSearchHitDTO,
    SearchKinopoiskFilmsLocalFirstService,
)
from services.catalog.search_rawg_catalog_games_service import SearchRawgCatalogGamesService
from services.catalog.youtube_video_dto import YoutubeVideoDTO
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


def _catalog_candidate(item: CatalogCandidateDTO) -> CatalogCandidateResponse:
    return CatalogCandidateResponse(
        candidate_id=item.candidate_id,
        provider=item.provider,
        external_id=item.external_id,
        kind=item.kind,
        kind_hint=item.kind_hint,
        title=item.title,
        subtitle=item.subtitle,
        cover_url=item.cover_url,
        catalog_item_id=item.catalog_item_id,
        source=item.source,
        degraded=item.degraded,
    )


def _community_page_response(
    page,
) -> CatalogCommunityCardsPageResponse:
    return CatalogCommunityCardsPageResponse(
        items=[
            CatalogCommunityCardItemResponse(
                id=item.id,
                author=CatalogCommunityAuthorResponse(
                    id=item.author.id,
                    profile_slug=item.author.profile_slug,
                    username=item.author.username,
                    first_name=item.author.first_name,
                    last_name=item.author.last_name,
                    photo_url=item.author.photo_url,
                    display_name=item.author.display_name,
                ),
                rating=item.rating,
                company=item.company,
                mood_before=item.mood_before,
                mood_after=item.mood_after,
                watch_note=item.watch_note,
                custom_tags=list(item.custom_tags),
                updated_at=item.updated_at,
                is_favorite=item.is_favorite,
            )
            for item in page.items
        ],
        next_cursor=page.next_cursor,
    )


@router.get(
    '/items/{catalog_item_id}',
    response_model=CatalogItemDetailResponse,
    summary='Метаданные элемента каталога для community hub',
)
async def get_catalog_item_detail(
    catalog_item_id: int,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CatalogItemDetailResponse:
    try:
        detail = await GetCatalogItemDetailService.build(db).execute(catalog_item_id)
    except GetCatalogItemDetailService.CatalogItemNotFound as e:
        raise HTTPException(status_code=404, detail='catalog item not found') from e

    my_card_id = await GetMyUserCardIdForCatalogItemService.build(db).execute(
        viewer.id,
        catalog_item_id,
    )
    return CatalogItemDetailResponse(
        catalog_item_id=detail.catalog_item_id,
        provider=detail.provider,
        external_id=detail.external_id,
        kind=detail.kind,
        title=detail.title,
        year=detail.year,
        poster_url=detail.poster_url,
        short_description=detail.short_description,
        description=detail.description,
        film_id=detail.film_id,
        game_id=detail.game_id,
        genres=list(detail.genres),
        my_card_id=my_card_id,
    )


@router.get(
    '/items/{catalog_item_id}/following-ratings',
    response_model=FollowingRatingsListResponse,
    summary='Оценки подписок для элемента каталога',
)
async def list_catalog_item_following_ratings(
    catalog_item_id: int,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FollowingRatingsListResponse:
    try:
        await GetCatalogItemDetailService.build(db).execute(catalog_item_id)
    except GetCatalogItemDetailService.CatalogItemNotFound as e:
        raise HTTPException(status_code=404, detail='catalog item not found') from e
    try:
        result = await ListFollowingRatingsForTitleService.build(db).execute(
            viewer.id,
            catalog_item_id=catalog_item_id,
        )
    except ListFollowingRatingsForTitleService.InvalidTitleRef:
        raise HTTPException(status_code=422, detail='invalid title ref') from None
    return following_ratings_list_response(result)


@router.get(
    '/items/{catalog_item_id}/community-cards',
    response_model=CatalogCommunityCardsPageResponse,
    summary='Публичные оценки пользователей по элементу каталога',
)
async def list_catalog_community_cards(
    catalog_item_id: int,
    _viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=50),
) -> CatalogCommunityCardsPageResponse:
    item = await db.get(CatalogItem, catalog_item_id)
    if item is None:
        raise HTTPException(status_code=404, detail='catalog item not found')
    try:
        page = await ListCatalogCommunityCardsService.build(db).execute(
            cursor,
            limit,
            catalog_item_id=catalog_item_id,
            film_id=item.film_id,
        )
    except ListCatalogCommunityCardsService.InvalidCursor:
        raise HTTPException(status_code=422, detail='invalid cursor') from None
    return _community_page_response(page)


@router.get(
    '/candidates',
    response_model=CatalogCandidatesResponse,
    summary='Смешанный поиск кандидатов каталога (Kinopoisk + RAWG)',
)
async def search_catalog_candidates(
    *,
    db: Annotated[AsyncSession, Depends(get_db)],
    _viewer: CurrentUser,
    q: Annotated[
        str,
        Query(
            min_length=1,
            alias='q',
            description='Поисковая строка; после нормализации ≥3 для kinopoisk, ≥4 для rawg',
        ),
    ],
    page: Annotated[int, Query(ge=1)] = 1,
    limit: Annotated[int, Query(ge=1, le=40)] = 15,
) -> CatalogCandidatesResponse:
    result = await SearchCatalogCandidatesService.build(db).execute(q, page=page, limit=limit)
    return CatalogCandidatesResponse(
        items=[_catalog_candidate(item) for item in result.items],
        has_more=result.has_more,
        meta=CatalogCandidatesMetaResponse(degraded_sources=list(result.degraded_sources)),
    )


@router.get(
    '/search', response_model=CatalogSearchResponse, summary='Поиск в каталоге (Kinopoisk / RAWG)'
)
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
            result = await SearchKinopoiskFilmsLocalFirstService.build(db).execute(
                keyword=keyword, page=page
            )
        except KinopoiskProviderTransport.KinopoiskProviderTransportError as e:
            raise HTTPException(status_code=502, detail=str(e)) from e

        sliced = tuple(result.hits[:limit])
        has_more = result.has_more or len(result.hits) > limit
        return CatalogSearchResponse(
            items=[_film_search_hit(hit) for hit in sliced], has_more=has_more
        )

    if len(keyword) < 4:
        raise HTTPException(
            status_code=422,
            detail='Query must contain at least 4 non-whitespace characters for RAWG search',
        )

    try:
        raw_result = await SearchRawgCatalogGamesService.build(db).execute(
            keyword, limit, page=page
        )
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


@router.post(
    '/resolve',
    response_model=CatalogResolveResponse,
    summary='Резолв элемента каталога по URL провайдера',
)
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

    my_card_id = await GetMyUserCardIdForLinkedFilmService.build(db).execute(viewer.id, film.id)
    award_badges = await film_award_badge_responses(db, film.id)

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
            primary_director_kinopoisk_id=film.primary_director_kinopoisk_id,
            primary_director_name=film.primary_director_name,
            title=film.title,
            year=film.year,
            poster_url=film.poster_url,
            short_description=film.short_description,
            description=film.description,
            my_card_id=my_card_id,
            award_badges=award_badges,
        ),
    )


@router.post(
    '/resolve-by-url',
    response_model=CatalogResolveByUrlResponse,
    summary='Резолв элемента каталога по URL (provider определяется по host)',
)
async def resolve_catalog_by_url(
    body: CatalogResolveByUrlRequest,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CatalogResolveByUrlResponse:
    try:
        result = await ResolveCatalogByUrlService.build(db).execute(url=body.url)
    except ResolveCatalogByUrlService.UnsupportedUrlHostError as e:
        raise HTTPException(status_code=422, detail='unsupported url host') from e
    except ResolveYoutubeVideoByUrlService.UnsupportedUrlError as e:
        raise HTTPException(status_code=422, detail='unsupported youtube url') from e
    except KinopoiskUrlParseError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except ResolveCatalogByUrlService.CatalogFilmNotFoundError as e:
        raise HTTPException(status_code=404, detail='catalog item not found') from e
    except ResolveCatalogByUrlService.UpstreamError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except KinopoiskClientError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e

    if isinstance(result, YoutubeVideoDTO):
        my_card_id = (
            await db.execute(
                select(UserCard.id).where(
                    UserCard.user_id == viewer.id,
                    UserCard.provider == CatalogProvider.youtube,
                    UserCard.external_id == result.video_id,
                )
            )
        ).scalar_one_or_none()
        return CatalogResolveByUrlResponse(
            provider=CatalogProvider.youtube,
            external_id=result.video_id,
            kind='video',
            title=result.title,
            cover_url=result.cover_url,
            summary=result.summary,
            catalog_item_id=None,
            film=None,
            source_url=result.canonical_url,
            my_card_id=int(my_card_id) if my_card_id is not None else None,
        )

    catalog_item, film = result
    my_card_id = await GetMyUserCardIdForLinkedFilmService.build(db).execute(viewer.id, film.id)
    award_badges = await film_award_badge_responses(db, film.id)

    return CatalogResolveByUrlResponse(
        catalog_item_id=catalog_item.id,
        provider=catalog_item.provider,
        external_id=catalog_item.external_id,
        kind='film',
        title=film.title,
        cover_url=film.poster_url,
        summary=film.short_description,
        film=FilmResponse(
            id=film.id,
            kinopoisk_id=film.kinopoisk_id,
            genres=list(film.genres or []),
            primary_director_kinopoisk_id=film.primary_director_kinopoisk_id,
            primary_director_name=film.primary_director_name,
            title=film.title,
            year=film.year,
            poster_url=film.poster_url,
            short_description=film.short_description,
            description=film.description,
            my_card_id=my_card_id,
            award_badges=award_badges,
        ),
        source_url=None,
        my_card_id=None,
    )
