from __future__ import annotations

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.cards.feed_post_feed_mapping import feed_post_feed_item_to_response
from api.cards.schemas import UserFeedPostsPageResponse
from api.profile.schemas import (
    MovieCardPageResponse,
    MyMovieCardTagStatItem,
    MyMovieCardTagStatsResponse,
    PublicProfileResponse,
    SubscriptionListResponse,
    UserMovieCardStatsResponse,
    WatchlistFilmPageResponse,
    build_movie_card_page_response,
    build_public_profile_response,
    build_subscription_list_response,
    build_user_movie_card_stats_response,
    build_watchlist_film_page_response,
)
from conf import settings
from core.database import get_db
from deps.auth import CurrentUser
from models.movie_card_enums import CardCompany, CardMoodAfter, CardMoodBefore
from models.user import User
from services.profile.get_public_user_by_id import GetPublicUserByIdService
from services.profile.get_user_movie_card_stats import GetUserMovieCardStatsService
from services.profile.get_user_profile_counts import GetUserProfileCountsService
from services.profile.list_my_movie_card_tag_stats import ListMyMovieCardTagStatsService
from services.profile.list_user_feed_posts import ListUserFeedPostsService
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
from services.watchlist.list_user_watchlist_films import ListUserWatchlistFilmsService

router = APIRouter(prefix='/users', tags=['users'])

ProfileCardsSort = Literal['recent', 'rating_desc', 'rating_asc']


def _normalize_filter_tags(raw: list[str] | None) -> list[str]:
    if not raw:
        return []
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        s = item.strip()
        if s == '' or len(s) > 80:
            continue
        key = s.lower()
        if key in seen:
            continue
        seen.add(key)
        out.append(s)
        if len(out) >= 8:
            break
    return out


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
    '/{user_id}/movie-card-tags',
    response_model=MyMovieCardTagStatsResponse,
    summary='Кастомные теги с карточек пользователя (частота) — для фильтра в профиле',
)
async def list_user_movie_card_tags(
    user_id: UUID,
    _viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=200, ge=1, le=500),
) -> MyMovieCardTagStatsResponse:
    exists = await GetPublicUserByIdService(db).execute(user_id)
    if exists is None:
        raise _not_found()
    cap = min(limit, 500)
    rows = await ListMyMovieCardTagStatsService(db).execute(user_id, limit=cap)
    return MyMovieCardTagStatsResponse(
        items=[MyMovieCardTagStatItem(tag=r.tag, use_count=r.use_count) for r in rows]
    )


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
    favorites_only: bool = Query(
        default=False,
        description='Только избранные: при sort=recent — по времени отметки; при rating_* — по оценке',
    ),
    sort: ProfileCardsSort = Query(
        default='recent',
        description='recent — новые первыми; rating_desc — выше оценка; rating_asc — ниже оценка',
    ),
    tag: list[str] | None = Query(
        default=None,
        description='Кастомный тег карточки; повтор параметра — пересечение (AND)',
    ),
    year_min: int | None = Query(default=None, ge=1874, le=2100),
    year_max: int | None = Query(default=None, ge=1874, le=2100),
    company: CardCompany | None = Query(default=None, description='С кем смотрел'),
    mood_before: CardMoodBefore | None = Query(default=None, description='Настроение до'),
    mood_after: CardMoodAfter | None = Query(default=None, description='Итог просмотра'),
    film_title: str | None = Query(
        default=None,
        max_length=120,
        description='Подстрока в названии фильма (только карточки этого пользователя, без внешних API)',
    ),
) -> MovieCardPageResponse:
    exists = await GetPublicUserByIdService(db).execute(user_id)
    if exists is None:
        raise _not_found()
    if year_min is not None and year_max is not None and year_min > year_max:
        raise HTTPException(status_code=422, detail='year_min must be <= year_max')
    cap = min(limit, 50)
    tags_norm = _normalize_filter_tags(tag)
    company_val = company.value if company is not None else None
    mood_before_val = mood_before.value if mood_before is not None else None
    mood_after_val = mood_after.value if mood_after is not None else None
    try:
        page = await ListUserMovieCardsService(db).execute(
            user_id,
            cursor,
            cap,
            favorites_only=favorites_only,
            sort=sort,
            tags_all=tags_norm,
            year_min=year_min,
            year_max=year_max,
            company=company_val,
            mood_before=mood_before_val,
            mood_after=mood_after_val,
            film_title_search=film_title,
        )
    except ListUserMovieCardsService.InvalidCursor:
        raise HTTPException(status_code=422, detail='invalid cursor') from None
    return build_movie_card_page_response(page)


@router.get(
    '/{user_id}/watchlist',
    response_model=WatchlistFilmPageResponse,
    summary='Фильмы в списке «к просмотру» (публично)',
)
async def list_user_watchlist_films(
    user_id: UUID,
    _viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1),
) -> WatchlistFilmPageResponse:
    exists = await GetPublicUserByIdService(db).execute(user_id)
    if exists is None:
        raise _not_found()
    cap = min(limit, 50)
    page = await ListUserWatchlistFilmsService(db).execute(user_id, cursor, cap)
    return build_watchlist_film_page_response(page)


@router.get(
    '/{user_id}/feed-posts',
    response_model=UserFeedPostsPageResponse,
    summary='Текстовые посты пользователя (вкладка «Посты» в профиле)',
)
async def list_user_feed_posts(
    user_id: UUID,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = None,
    limit: int = Query(default=20, ge=1, le=50),
) -> UserFeedPostsPageResponse:
    exists = await GetPublicUserByIdService(db).execute(user_id)
    if exists is None:
        raise _not_found()
    cap = min(limit, 50)
    try:
        page = await ListUserFeedPostsService(db).execute(user_id, cursor, cap, viewer.id)
    except ListUserFeedPostsService.InvalidCursor:
        raise HTTPException(status_code=422, detail='invalid cursor') from None
    return UserFeedPostsPageResponse(
        items=[feed_post_feed_item_to_response(it) for it in page.items],
        next_cursor=page.next_cursor,
    )


@router.get(
    '/{user_id}/stats',
    response_model=UserMovieCardStatsResponse,
    summary='Агрегированная статистика карточек фильмов пользователя',
)
async def get_user_movie_card_stats(
    user_id: UUID,
    _viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserMovieCardStatsResponse:
    exists = await GetPublicUserByIdService(db).execute(user_id)
    if exists is None:
        raise _not_found()
    stats = await GetUserMovieCardStatsService(db).execute(user_id)
    return build_user_movie_card_stats_response(stats)


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
