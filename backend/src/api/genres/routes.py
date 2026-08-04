from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.genres.schemas import (
    GenreCatalogItemResponse,
    GenreFilmItemResponse,
    GenreFilmsPageResponse,
    GenresCatalogPageResponse,
    GenreSummaryResponse,
)
from core.database import get_db
from deps.auth import CurrentUser
from services.genres.get_genre_summary import GetGenreSummaryService
from services.genres.list_genre_rated_films import ListGenreRatedFilmsService
from services.genres.list_genres_catalog import ListGenresCatalogService

router = APIRouter(prefix='/genres', tags=['genres'])


@router.get('', response_model=GenresCatalogPageResponse, summary='Каталог жанров Filmony')
async def list_genres_catalog(
    _viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
) -> GenresCatalogPageResponse:
    try:
        page = await ListGenresCatalogService.build(db).execute(cursor, limit)
    except ListGenresCatalogService.InvalidCursor:
        raise HTTPException(status_code=422, detail='invalid cursor') from None
    return GenresCatalogPageResponse(
        items=[
            GenreCatalogItemResponse(slug=item.slug, genre=item.genre, films_count=item.films_count)
            for item in page.items
        ],
        next_cursor=page.next_cursor,
    )


@router.get(
    '/{slug}',
    response_model=GenreSummaryResponse,
    summary='Сводка по жанру (фильмы с оценками в Filmony)',
)
async def get_genre_summary(
    slug: str,
    _viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GenreSummaryResponse:
    try:
        summary = await GetGenreSummaryService.build(db).execute(slug)
    except GetGenreSummaryService.GenreNotFound:
        raise HTTPException(status_code=404, detail='genre not found') from None
    return GenreSummaryResponse(
        slug=summary.slug,
        genre=summary.genre,
        films_count=summary.films_count,
        avg_community_rating=summary.avg_community_rating,
        top_genres=list(summary.top_genres),
    )


@router.get(
    '/{slug}/films',
    response_model=GenreFilmsPageResponse,
    summary='Фильмы жанра с хотя бы одной оценкой в Filmony',
)
async def list_genre_films(
    slug: str,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=50),
) -> GenreFilmsPageResponse:
    viewer_id: UUID | None = viewer.id
    try:
        page = await ListGenreRatedFilmsService.build(db).execute(
            slug,
            cursor,
            limit,
            viewer_user_id=viewer_id,
        )
    except ListGenreRatedFilmsService.InvalidCursor:
        raise HTTPException(status_code=422, detail='invalid cursor') from None
    except ListGenreRatedFilmsService.GenreNotFound:
        raise HTTPException(status_code=404, detail='genre not found') from None
    if not page.items and cursor is None:
        try:
            await GetGenreSummaryService.build(db).execute(slug)
        except GetGenreSummaryService.GenreNotFound:
            raise HTTPException(status_code=404, detail='genre not found') from None
    return GenreFilmsPageResponse(
        items=[
            GenreFilmItemResponse(
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
