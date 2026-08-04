from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.directors.schemas import (
    DirectorCatalogItemResponse,
    DirectorFilmItemResponse,
    DirectorFilmsPageResponse,
    DirectorsCatalogPageResponse,
    DirectorSummaryResponse,
)
from core.database import get_db
from deps.auth import CurrentUser
from services.directors.get_director_summary import GetDirectorSummaryService
from services.directors.list_director_rated_films import ListDirectorRatedFilmsService
from services.directors.list_directors_catalog import ListDirectorsCatalogService

router = APIRouter(prefix='/directors', tags=['directors'])


@router.get(
    '',
    response_model=DirectorsCatalogPageResponse,
    summary='Каталог режиссёров с оценёнными фильмами в Filmony',
)
async def list_directors_catalog(
    _viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
) -> DirectorsCatalogPageResponse:
    try:
        page = await ListDirectorsCatalogService.build(db).execute(cursor, limit)
    except ListDirectorsCatalogService.InvalidCursor:
        raise HTTPException(status_code=422, detail='invalid cursor') from None
    return DirectorsCatalogPageResponse(
        items=[
            DirectorCatalogItemResponse(
                kinopoisk_id=item.kinopoisk_id,
                name=item.name,
                films_count=item.films_count,
            )
            for item in page.items
        ],
        next_cursor=page.next_cursor,
    )


@router.get(
    '/{kinopoisk_id}',
    response_model=DirectorSummaryResponse,
    summary='Сводка по режиссёру (фильмы с оценками в Filmony)',
)
async def get_director_summary(
    kinopoisk_id: int,
    _viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> DirectorSummaryResponse:
    if kinopoisk_id < 1:
        raise HTTPException(status_code=422, detail='invalid kinopoisk_id')
    try:
        summary = await GetDirectorSummaryService.build(db).execute(kinopoisk_id)
    except GetDirectorSummaryService.DirectorNotFound:
        raise HTTPException(status_code=404, detail='director not found') from None
    return DirectorSummaryResponse(
        kinopoisk_id=summary.kinopoisk_id,
        name=summary.name,
        films_count=summary.films_count,
        avg_community_rating=summary.avg_community_rating,
    )


@router.get(
    '/{kinopoisk_id}/films',
    response_model=DirectorFilmsPageResponse,
    summary='Фильмы режиссёра с хотя бы одной оценкой в Filmony',
)
async def list_director_films(
    kinopoisk_id: int,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=50),
) -> DirectorFilmsPageResponse:
    if kinopoisk_id < 1:
        raise HTTPException(status_code=422, detail='invalid kinopoisk_id')
    viewer_id: UUID | None = viewer.id
    try:
        page = await ListDirectorRatedFilmsService.build(db).execute(
            kinopoisk_id,
            cursor,
            limit,
            viewer_user_id=viewer_id,
        )
    except ListDirectorRatedFilmsService.InvalidCursor:
        raise HTTPException(status_code=422, detail='invalid cursor') from None
    if not page.items and cursor is None:
        try:
            await GetDirectorSummaryService.build(db).execute(kinopoisk_id)
        except GetDirectorSummaryService.DirectorNotFound:
            raise HTTPException(status_code=404, detail='director not found') from None
    return DirectorFilmsPageResponse(
        items=[
            DirectorFilmItemResponse(
                film_id=item.film_id,
                title=item.title,
                year=item.year,
                poster_url=item.poster_url,
                genres=list(item.genres),
                community_avg_rating=item.community_avg_rating,
                ratings_count=item.ratings_count,
                my_card_id=item.my_card_id,
            )
            for item in page.items
        ],
        next_cursor=page.next_cursor,
    )
