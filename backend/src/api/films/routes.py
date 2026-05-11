from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.films.schemas import FilmResolveRequest, FilmResponse
from core.database import get_db
from deps.auth import CurrentUser
from services.cards.get_my_movie_card_id_for_film import GetMyMovieCardIdForFilmService
from services.films.get_film_by_id import GetFilmByIdService
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
