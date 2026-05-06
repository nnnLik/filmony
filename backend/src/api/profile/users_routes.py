from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.profile.schemas import (
    MovieCardPageResponse,
    PublicProfileResponse,
    build_movie_card_page_response,
    build_public_profile_response,
)
from conf import settings
from core.database import get_db
from deps.auth import CurrentUser
from models.user import User
from services.profile.get_public_user_by_id import GetPublicUserByIdService
from services.profile.get_public_user_by_slug import GetPublicUserBySlugService
from services.profile.get_user_profile_counts import GetUserProfileCountsService
from services.profile.list_user_movie_cards import ListUserMovieCardsService

router = APIRouter(prefix='/users', tags=['users'])

_PRIVACY_DOC = (
    'Публичный профиль доступен любому пользователю с валидной сессией. '
    'Несуществующий пользователь отдаётся как 404 (без утечки факта существования slug/id в смежных сценариях).'
)


def _not_found() -> HTTPException:
    return HTTPException(status_code=404, detail='user not found')


async def _public_profile_or_404(
    target: User | None,
) -> PublicProfileResponse:
    if target is None:
        raise _not_found()
    counts = await GetUserProfileCountsService().execute(target.id)
    return build_public_profile_response(target, counts)


@router.get(
    '/by-slug/{slug}',
    response_model=PublicProfileResponse,
    summary='Публичный профиль по slug',
    description=_PRIVACY_DOC,
)
async def get_user_by_slug(
    slug: str,
    _viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PublicProfileResponse:
    user = await GetPublicUserBySlugService(db).execute(slug)
    return await _public_profile_or_404(user)


@router.get(
    '/{user_id}',
    response_model=PublicProfileResponse,
    summary='Публичный профиль по внутреннему id',
    description=_PRIVACY_DOC,
)
async def get_user_by_id(
    user_id: UUID,
    _viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PublicProfileResponse:
    user = await GetPublicUserByIdService(db).execute(user_id)
    return await _public_profile_or_404(user)


@router.get(
    '/{user_id}/cards',
    response_model=MovieCardPageResponse,
    summary='Карточки фильмов пользователя (пагинация; v1 — пустой список)',
)
async def list_user_cards(
    user_id: UUID,
    _viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = None,
    limit: int = Query(default=settings.profile.page_size_default, ge=1),
) -> MovieCardPageResponse:
    exists = await GetPublicUserByIdService(db).execute(user_id)
    if exists is None:
        raise _not_found()
    cap = min(limit, settings.profile.page_size_max)
    page = await ListUserMovieCardsService().execute(user_id, cursor, cap)
    return build_movie_card_page_response(page)
