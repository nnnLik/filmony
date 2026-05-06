from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.films.schemas import FilmResolveRequest, FilmResponse
from core.database import get_db
from deps.auth import CurrentUser
from models.film import Film
from services.kinopoisk.resolve_kinopoisk_film import (
    KinopoiskClientError,
    KinopoiskUrlParseError,
    ResolveKinopoiskFilmService,
)

router = APIRouter(prefix='/films', tags=['films'])


@router.post('/resolve', response_model=FilmResponse, summary='Резолв фильма по ссылке Кинопоиска')
async def resolve_film(
    body: FilmResolveRequest,
    _viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FilmResponse:
    try:
        film = await ResolveKinopoiskFilmService(db).execute(body.url)
    except KinopoiskUrlParseError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except KinopoiskClientError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    return FilmResponse(
        id=film.id,
        kinopoisk_id=film.kinopoisk_id,
        genres=list(film.genres or []),
        title=film.title,
        year=film.year,
        poster_url=film.poster_url,
    )


@router.get('/{film_id}', response_model=FilmResponse, summary='Получить фильм по id')
async def get_film(
    film_id: int,
    _viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FilmResponse:
    result = await db.execute(select(Film).where(Film.id == film_id))
    film = result.scalar_one_or_none()
    if film is None:
        raise HTTPException(status_code=404, detail='film not found')
    return FilmResponse(
        id=film.id,
        kinopoisk_id=film.kinopoisk_id,
        genres=list(film.genres or []),
        title=film.title,
        year=film.year,
        poster_url=film.poster_url,
    )
