from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.profile.schemas import (
    MovieCardPageResponse,
    PublicProfileResponse,
    SubscriptionListResponse,
    build_movie_card_page_response,
    build_public_profile_response,
    build_subscription_list_response,
)
from conf import settings
from core.database import get_db
from deps.auth import CurrentUser
from models.user import User
from services.profile.get_public_user_by_id import GetPublicUserByIdService
from services.profile.get_user_profile_counts import GetUserProfileCountsService
from services.profile.list_user_movie_cards import ListUserMovieCardsService
from services.subscriptions.create_user_subscription import (
    CreateUserSubscriptionService,
    SelfSubscriptionError,
    UserAlreadySubscribedError,
)
from services.subscriptions.create_user_subscription import (
    TargetUserNotFoundError as SubscriptionTargetUserNotFoundCreateError,
)
from services.subscriptions.delete_user_subscription import (
    DeleteUserSubscriptionService,
    SubscriptionNotFoundError,
)
from services.subscriptions.delete_user_subscription import (
    TargetUserNotFoundError as SubscriptionTargetUserNotFoundDeleteError,
)
from services.subscriptions.list_user_subscriptions import (
    ListUserSubscriptionsService,
    SubscriptionListType,
)
from services.subscriptions.list_user_subscriptions import (
    TargetUserNotFoundError as SubscriptionTargetUserNotFoundListError,
)

router = APIRouter(prefix='/users', tags=['users'])

_PRIVACY_DOC = (
    'Публичный профиль доступен любому пользователю с валидной сессией. '
    'Несуществующий пользователь отдаётся как 404 (без утечки факта существования slug/id в смежных сценариях).'
)


def _not_found() -> HTTPException:
    return HTTPException(status_code=404, detail='user not found')


async def _public_profile_or_404(
    target: User | None,
    db: AsyncSession,
) -> PublicProfileResponse:
    if target is None:
        raise _not_found()
    counts = await GetUserProfileCountsService(db).execute(target.id)
    return build_public_profile_response(target, counts)


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
    return await _public_profile_or_404(user, db)


@router.get(
    '/{user_id}/cards',
    response_model=MovieCardPageResponse,
    summary='Карточки фильмов пользователя (пагинация)',
)
async def list_user_cards(
    user_id: UUID,
    _viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1),
) -> MovieCardPageResponse:
    exists = await GetPublicUserByIdService(db).execute(user_id)
    if exists is None:
        raise _not_found()
    cap = min(limit, 50)
    page = await ListUserMovieCardsService(db).execute(user_id, cursor, cap)
    return build_movie_card_page_response(page)


@router.post(
    '/{user_id}/subscriptions',
    status_code=204,
    response_class=Response,
    summary='Подписаться на пользователя',
)
async def create_subscription(
    user_id: UUID,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    try:
        await CreateUserSubscriptionService(db).execute(viewer.id, user_id)
    except SelfSubscriptionError:
        raise HTTPException(status_code=422, detail='cannot subscribe to self') from None
    except SubscriptionTargetUserNotFoundCreateError:
        raise _not_found() from None
    except UserAlreadySubscribedError:
        raise HTTPException(status_code=409, detail='subscription already exists') from None
    return Response(status_code=204)


@router.delete(
    '/{user_id}/subscriptions',
    status_code=204,
    response_class=Response,
    summary='Отписаться от пользователя',
)
async def delete_subscription(
    user_id: UUID,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    try:
        await DeleteUserSubscriptionService(db).execute(viewer.id, user_id)
    except SubscriptionTargetUserNotFoundDeleteError:
        raise _not_found() from None
    except SubscriptionNotFoundError:
        raise HTTPException(status_code=404, detail='subscription not found') from None
    return Response(status_code=204)


@router.get(
    '/{user_id}/subscriptions',
    response_model=SubscriptionListResponse,
    summary='Список подписчиков/подписок пользователя',
)
async def list_subscriptions(
    user_id: UUID,
    _viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    relation: SubscriptionListType = Query(default=SubscriptionListType.both, alias='type'),
) -> SubscriptionListResponse:
    try:
        items = await ListUserSubscriptionsService(db).execute(user_id, relation)
    except SubscriptionTargetUserNotFoundListError:
        raise _not_found() from None
    return build_subscription_list_response(items)
