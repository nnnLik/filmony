from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.franchises.schemas import (
    FranchiseFilmItemResponse,
    FranchiseFilmsPageResponse,
    FranchiseSummaryResponse,
)
from core.database import get_db
from deps.auth import CurrentUser
from services.franchises.get_franchise_summary import GetFranchiseSummaryService
from services.franchises.list_franchise_rated_films import ListFranchiseRatedFilmsService

router = APIRouter(prefix='/franchises', tags=['franchises'])


@router.get(
    '/{franchise_key:path}/films',
    response_model=FranchiseFilmsPageResponse,
    summary='Фильмы франшизы с хотя бы одной оценкой в Filmony',
)
async def list_franchise_films(
    franchise_key: str,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=50),
) -> FranchiseFilmsPageResponse:
    viewer_id: UUID | None = viewer.id
    try:
        page = await ListFranchiseRatedFilmsService.build(db).execute(
            franchise_key,
            cursor,
            limit,
            viewer_user_id=viewer_id,
        )
    except ListFranchiseRatedFilmsService.InvalidCursor:
        raise HTTPException(status_code=422, detail='invalid cursor') from None
    if not page.items and cursor is None:
        try:
            await GetFranchiseSummaryService.build(db).execute(franchise_key)
        except GetFranchiseSummaryService.FranchiseNotFound:
            raise HTTPException(status_code=404, detail='franchise not found') from None
    return FranchiseFilmsPageResponse(
        items=[
            FranchiseFilmItemResponse(
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


@router.get(
    '/{franchise_key:path}',
    response_model=FranchiseSummaryResponse,
    summary='Сводка по франшизе (фильмы с оценками в Filmony)',
)
async def get_franchise_summary(
    franchise_key: str,
    _viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FranchiseSummaryResponse:
    try:
        summary = await GetFranchiseSummaryService.build(db).execute(franchise_key)
    except GetFranchiseSummaryService.FranchiseNotFound:
        raise HTTPException(status_code=404, detail='franchise not found') from None
    return FranchiseSummaryResponse(
        franchise_key=summary.franchise_key,
        label=summary.label,
        films_count=summary.films_count,
        avg_community_rating=summary.avg_community_rating,
    )
