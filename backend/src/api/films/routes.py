from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.films.schemas import (
    FilmCommunityAuthorResponse,
    FilmCommunityCardItemResponse,
    FilmCommunityCardsPageResponse,
    FilmResolveRequest,
    FilmResponse,
)
from core.database import get_db
from deps.auth import CurrentUser
from services.cards.get_my_movie_card_id_for_film import GetMyMovieCardIdForFilmService
from services.films.get_film_by_id import GetFilmByIdService
from services.films.list_film_community_cards import ListFilmCommunityCardsService
from services.kinopoisk.resolve_kinopoisk_film import (
    KinopoiskClientError,
    KinopoiskUrlParseError,
    ResolveKinopoiskFilmService,
)

router = APIRouter(prefix='/films', tags=['films'])


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
    my_card_id = await GetMyMovieCardIdForFilmService.build(db).execute(viewer.id, film.id)
    return FilmResponse(
        id=film.id,
        kinopoisk_id=film.kinopoisk_id,
        genres=list(film.genres or []),
        title=film.title,
        year=film.year,
        poster_url=film.poster_url,
        short_description=film.short_description,
        description=film.description,
        my_card_id=my_card_id,
    )


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


@router.get('/{film_id}', response_model=FilmResponse, summary='Получить фильм по id')
async def get_film(
    film_id: int,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FilmResponse:
    film = await GetFilmByIdService(db).execute(film_id)
    if film is None:
        raise HTTPException(status_code=404, detail='film not found')
    my_card_id = await GetMyMovieCardIdForFilmService.build(db).execute(viewer.id, film.id)
    return FilmResponse(
        id=film.id,
        kinopoisk_id=film.kinopoisk_id,
        genres=list(film.genres or []),
        title=film.title,
        year=film.year,
        poster_url=film.poster_url,
        short_description=film.short_description,
        description=film.description,
        my_card_id=my_card_id,
    )
