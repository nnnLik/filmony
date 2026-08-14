from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.cards.schemas import FollowingRatingsListResponse
from api.collections.schemas import (
    CollectionListResponse,
    CollectionSummaryResponse,
    UserCollectionProgressResponse,
)
from api.films.award_badges import film_award_badge_responses
from api.films.mappers import film_passport_response_fields
from api.films.schemas import (
    FilmCommunityAuthorResponse,
    FilmCommunityCardItemResponse,
    FilmCommunityCardsPageResponse,
    FilmPlaybackResponse,
    FilmResolveRequest,
    FilmResponse,
)
from core.database import get_db
from deps.auth import CurrentUser
from services.cards.following_ratings_response import following_ratings_list_response
from services.cards.get_my_user_card_id_for_linked_film import GetMyUserCardIdForLinkedFilmService
from services.cards.list_following_ratings_for_title import ListFollowingRatingsForTitleService
from services.collections.list_collections import CollectionSummaryDTO
from services.collections.list_film_collections import ListFilmCollectionsService
from services.films.get_film_by_id import GetFilmByIdService
from services.films.list_film_community_cards import ListFilmCommunityCardsService
from services.films.resolve_film_playback import FilmPlaybackDTO, ResolveFilmPlaybackService
from services.franchises.franchise_label import resolve_franchise_label
from services.kinopoisk.resolve_kinopoisk_film import (
    KinopoiskClientError,
    KinopoiskUrlParseError,
    ResolveKinopoiskFilmService,
)

router = APIRouter(prefix='/films', tags=['films'])


def _film_playback_response(dto: FilmPlaybackDTO) -> FilmPlaybackResponse:
    return FilmPlaybackResponse(
        provider=dto.provider,
        title=dto.title,
        iframe_url=dto.iframe_url,
        film_id=dto.film_id,
        kinopoisk_id=dto.kinopoisk_id,
        expires_at=dto.expires_at,
    )


def _collection_progress_response(
    dto: CollectionSummaryDTO,
) -> UserCollectionProgressResponse | None:
    if dto.viewer_progress is None:
        return None
    return UserCollectionProgressResponse(
        rated_count=dto.viewer_progress.rated_count,
        total_count=dto.viewer_progress.total_count,
        completed_at=dto.viewer_progress.completed_at,
    )


def _collection_summary_response(dto: CollectionSummaryDTO) -> CollectionSummaryResponse:
    return CollectionSummaryResponse(
        slug=dto.slug,
        kind=dto.kind,
        title=dto.title,
        description=dto.description,
        season_year=dto.season_year,
        film_count=dto.film_count,
        content_updated_at=dto.content_updated_at,
        viewer_progress=_collection_progress_response(dto),
        is_pinned=dto.is_pinned,
    )


async def _film_response(db: AsyncSession, film, viewer_id) -> FilmResponse:
    my_card_id = await GetMyUserCardIdForLinkedFilmService.build(db).execute(viewer_id, film.id)
    franchise_label = None
    if film.franchise_key:
        franchise_label = await resolve_franchise_label(db, str(film.franchise_key))
    award_badges = await film_award_badge_responses(db, film.id)
    return FilmResponse(
        id=film.id,
        kinopoisk_id=film.kinopoisk_id,
        genres=list(film.genres or []),
        primary_director_kinopoisk_id=film.primary_director_kinopoisk_id,
        primary_director_name=film.primary_director_name,
        primary_director_poster_url=film.primary_director_poster_url,
        primary_director_tmdb_id=film.primary_director_tmdb_id,
        imdb_id=film.imdb_id,
        tmdb_id=film.tmdb_id,
        franchise_key=film.franchise_key,
        franchise_label=franchise_label,
        title=film.title,
        year=film.year,
        poster_url=film.poster_url,
        short_description=film.short_description,
        description=film.description,
        my_card_id=my_card_id,
        award_badges=award_badges,
        **film_passport_response_fields(film),
    )


@router.post('/resolve', response_model=FilmResponse, summary='Резолв фильма по ссылке Кинопоиска')
async def resolve_film(
    body: FilmResolveRequest,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FilmResponse:
    try:
        film = await ResolveKinopoiskFilmService(db).execute(body.url)
    except KinopoiskUrlParseError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except KinopoiskClientError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    return await _film_response(db, film, viewer.id)


@router.get(
    '/{film_id}/community-cards',
    response_model=FilmCommunityCardsPageResponse,
    summary='Публичные оценки пользователей по тайтлу из каталога',
)
async def list_film_community_cards(
    film_id: int,
    _viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=50),
) -> FilmCommunityCardsPageResponse:
    film = await GetFilmByIdService(db).execute(film_id)
    if film is None:
        raise HTTPException(status_code=404, detail='film not found')
    try:
        page = await ListFilmCommunityCardsService.build(db).execute(film_id, cursor, limit)
    except ListFilmCommunityCardsService.InvalidCursor:
        raise HTTPException(status_code=422, detail='invalid cursor') from None
    return FilmCommunityCardsPageResponse(
        items=[
            FilmCommunityCardItemResponse(
                id=item.id,
                author=FilmCommunityAuthorResponse(
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
                custom_tags=item.custom_tags,
                updated_at=item.updated_at,
                is_favorite=item.is_favorite,
            )
            for item in page.items
        ],
        next_cursor=page.next_cursor,
    )


@router.get(
    '/{film_id}/collections',
    response_model=CollectionListResponse,
    summary='Активные коллекции, в которых есть фильм',
)
async def list_film_collections(
    film_id: int,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CollectionListResponse:
    film = await GetFilmByIdService(db).execute(film_id)
    if film is None:
        raise HTTPException(status_code=404, detail='film not found')
    items = await ListFilmCollectionsService.build(db).execute(
        film_id,
        viewer_user_id=viewer.id,
    )
    return CollectionListResponse(items=[_collection_summary_response(item) for item in items])


@router.get(
    '/{film_id}/following-ratings',
    response_model=FollowingRatingsListResponse,
    summary='Оценки подписок для фильма',
)
async def list_film_following_ratings(
    film_id: int,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FollowingRatingsListResponse:
    film = await GetFilmByIdService(db).execute(film_id)
    if film is None:
        raise HTTPException(status_code=404, detail='film not found')
    try:
        result = await ListFollowingRatingsForTitleService.build(db).execute(
            viewer.id,
            film_id=film_id,
        )
    except ListFollowingRatingsForTitleService.InvalidTitleRef:
        raise HTTPException(status_code=422, detail='invalid title ref') from None
    return following_ratings_list_response(result)


@router.get(
    '/{film_id}/playback',
    response_model=FilmPlaybackResponse,
    summary='Получить embed-источник для просмотра фильма',
)
async def get_film_playback(
    film_id: int,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FilmPlaybackResponse:
    try:
        dto = await ResolveFilmPlaybackService.build(db).execute(film_id, viewer.id)
    except ResolveFilmPlaybackService.FilmNotFound:
        raise HTTPException(status_code=404, detail='film_not_found') from None
    except ResolveFilmPlaybackService.PlaybackUnavailable:
        raise HTTPException(status_code=422, detail='playback_unavailable') from None
    except ResolveFilmPlaybackService.PlaybackProviderError:
        raise HTTPException(status_code=502, detail='playback_provider_error') from None
    return _film_playback_response(dto)


@router.get('/{film_id}', response_model=FilmResponse, summary='Получить фильм по id')
async def get_film(
    film_id: int,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FilmResponse:
    film = await GetFilmByIdService(db).execute(film_id)
    if film is None:
        raise HTTPException(status_code=404, detail='film not found')
    return await _film_response(db, film, viewer.id)
