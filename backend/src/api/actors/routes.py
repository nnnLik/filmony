from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.actors.schemas import (
    ActorFilmItemResponse,
    ActorFilmsPageResponse,
    ActorSummaryResponse,
)
from core.database import get_db
from deps.auth import CurrentUser
from services.actors.get_actor_summary import GetActorSummaryService
from services.actors.list_actor_rated_films import ListActorRatedFilmsService
from services.profile.get_public_user_by_id import GetPublicUserByIdService

router = APIRouter(prefix='/actors', tags=['actors'])


async def _resolve_owner_user_id(
    viewer: CurrentUser,
    db: AsyncSession,
    user_id: UUID | None,
) -> UUID:
    owner_id = user_id if user_id is not None else viewer.id
    exists = await GetPublicUserByIdService(db).execute(owner_id)
    if exists is None:
        raise HTTPException(status_code=404, detail='user not found')
    return owner_id


@router.get(
    '/{kinopoisk_id}',
    response_model=ActorSummaryResponse,
    summary='Сводка по актёру для оценённых фильмов пользователя',
)
async def get_actor_summary(
    kinopoisk_id: int,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    user_id: UUID | None = Query(default=None, description='Владелец профиля (оценённые фильмы)'),
) -> ActorSummaryResponse:
    if kinopoisk_id < 1:
        raise HTTPException(status_code=422, detail='invalid kinopoisk_id')
    owner_id = await _resolve_owner_user_id(viewer, db, user_id)
    try:
        summary = await GetActorSummaryService.build(db).execute(
            kinopoisk_id,
            user_id=owner_id,
        )
    except GetActorSummaryService.ActorNotFound:
        raise HTTPException(status_code=404, detail='actor not found') from None
    return ActorSummaryResponse(
        kinopoisk_id=summary.kinopoisk_id,
        name=summary.name,
        poster_url=summary.poster_url,
        films_count=summary.films_count,
    )


@router.get(
    '/{kinopoisk_id}/films',
    response_model=ActorFilmsPageResponse,
    summary='Оценённые фильмы пользователя с участием актёра',
)
async def list_actor_films(
    kinopoisk_id: int,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=50),
    user_id: UUID | None = Query(default=None, description='Владелец профиля (оценённые фильмы)'),
) -> ActorFilmsPageResponse:
    if kinopoisk_id < 1:
        raise HTTPException(status_code=422, detail='invalid kinopoisk_id')
    owner_id = await _resolve_owner_user_id(viewer, db, user_id)
    try:
        page = await ListActorRatedFilmsService.build(db).execute(
            kinopoisk_id,
            cursor,
            limit,
            user_id=owner_id,
            viewer_user_id=viewer.id,
        )
    except ListActorRatedFilmsService.InvalidCursor:
        raise HTTPException(status_code=422, detail='invalid cursor') from None
    except ListActorRatedFilmsService.ActorNotFound:
        raise HTTPException(status_code=404, detail='actor not found') from None
    if not page.items and cursor is None:
        try:
            await GetActorSummaryService.build(db).execute(kinopoisk_id, user_id=owner_id)
        except GetActorSummaryService.ActorNotFound:
            raise HTTPException(status_code=404, detail='actor not found') from None
    return ActorFilmsPageResponse(
        items=[
            ActorFilmItemResponse(
                film_id=item.film_id,
                title=item.title,
                year=item.year,
                poster_url=item.poster_url,
                genres=list(item.genres),
                role=item.role,
                my_card_id=item.my_card_id,
                rating=item.rating,
                rated_at=item.rated_at.isoformat() if item.rated_at is not None else None,
            )
            for item in page.items
        ],
        next_cursor=page.next_cursor,
    )
