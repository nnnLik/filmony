from __future__ import annotations

import datetime as dt
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.profile.schemas import (
    MyProfileResponse,
    MyUserCardCategoryCreateRequest,
    MyUserCardCategoryListResponse,
    MyUserCardCategoryRenameRequest,
    MyUserCardCategoryResponse,
    MyUserCardTagStatItem,
    MyUserCardTagStatsResponse,
    PlannedUserCardResponse,
    ProfileUpdateRequest,
    UserCardsExportCsvResponse,
    WatchlistEntryItemResponse,
    WatchlistFilmCreateRequest,
    WatchlistMembershipResponse,
    build_my_profile_response,
    build_watchlist_entry_item_response,
)
from conf import settings
from core.database import get_db
from deps.auth import CurrentUser
from models.catalog_item import CatalogProvider
from models.film import Film
from services.cards.get_planned_user_card import GetPlannedUserCardService
from services.profile.export_my_user_cards_csv_telegram import ExportMyUserCardsCsvTelegramService
from services.profile.get_user_profile_counts import GetUserProfileCountsService
from services.profile.list_my_user_card_tag_stats import ListMyUserCardTagStatsService
from services.profile.update_my_profile import UpdateMyProfileService
from services.telegram.send_bot_message import SendTelegramBotMessageService
from services.user_card_categories.create_user_card_category import (
    CreateUserCardCategoryService,
)
from services.user_card_categories.list_my_user_card_categories import (
    ListMyUserCardCategoriesService,
)
from services.user_card_categories.rename_user_card_category import (
    RenameUserCardCategoryService,
)
from services.watchlist.create_watchlist_entry import CreateWatchlistEntryService
from services.watchlist.create_watchlist_entry_from_catalog import (
    CreateWatchlistEntryFromCatalogService,
)
from services.watchlist.create_watchlist_entry_from_film import (
    CreateWatchlistEntryFromFilmService,
)
from services.watchlist.delete_watchlist_entry import DeleteWatchlistEntryService
from services.watchlist.get_my_watchlist_presence import GetMyWatchlistPresenceService
from services.watchlist.list_user_watchlist_entries import ListUserWatchlistEntriesService
from services.watchlist.watchlist_card_id import watchlist_card_id_for_provider

router = APIRouter(prefix='/me', tags=['profile'])


async def _hydrated_entry_response(
    db: AsyncSession,
    user_id: UUID,
    entry_id: int,
) -> WatchlistEntryItemResponse:
    item = await ListUserWatchlistEntriesService(db).execute_for_entry(user_id, entry_id)
    if item is None:
        raise HTTPException(status_code=500, detail='watchlist entry missing after create')
    return build_watchlist_entry_item_response(item)


@router.get(
    '/card-categories',
    response_model=MyUserCardCategoryListResponse,
    summary='Мои категории/полки для карточек',
)
async def list_my_card_categories(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MyUserCardCategoryListResponse:
    rows = await ListMyUserCardCategoriesService.build(db).execute(user.id)
    return MyUserCardCategoryListResponse(
        items=[
            MyUserCardCategoryResponse(id=r.id, name=r.name, created_at=r.created_at) for r in rows
        ]
    )


@router.post(
    '/card-categories',
    response_model=MyUserCardCategoryResponse,
    summary='Создать категорию карточек',
)
async def create_my_card_category(
    body: MyUserCardCategoryCreateRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MyUserCardCategoryResponse:
    try:
        row = await CreateUserCardCategoryService.build(db).execute(user.id, body.name)
    except CreateUserCardCategoryService.CategoryValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except CreateUserCardCategoryService.DuplicateCategoryNameError:
        raise HTTPException(status_code=409, detail='category already exists') from None
    return MyUserCardCategoryResponse(id=row.id, name=row.name, created_at=row.created_at)


@router.patch(
    '/card-categories/{category_id}',
    response_model=MyUserCardCategoryResponse,
    summary='Переименовать категорию карточек',
)
async def rename_my_card_category(
    category_id: int,
    body: MyUserCardCategoryRenameRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MyUserCardCategoryResponse:
    try:
        row = await RenameUserCardCategoryService.build(db).execute(user.id, category_id, body.name)
    except RenameUserCardCategoryService.CategoryNotFoundError:
        raise HTTPException(status_code=404, detail='category not found') from None
    except RenameUserCardCategoryService.CategoryValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except RenameUserCardCategoryService.DuplicateCategoryNameError:
        raise HTTPException(status_code=409, detail='category name already exists') from None
    return MyUserCardCategoryResponse(id=row.id, name=row.name, created_at=row.created_at)


@router.get(
    '/movie-card-tags',
    response_model=MyUserCardTagStatsResponse,
    summary='Теги с карточек текущего пользователя (частота) для автодополнения',
)
async def get_my_movie_card_tags(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    limit: int = Query(default=400, ge=1, le=500),
) -> MyUserCardTagStatsResponse:
    rows = await ListMyUserCardTagStatsService(db).execute(user.id, limit=limit)
    return MyUserCardTagStatsResponse(
        items=[MyUserCardTagStatItem(tag=r.tag, use_count=r.use_count) for r in rows]
    )


@router.get(
    '/profile',
    response_model=MyProfileResponse,
    summary='Текущий пользователь: полный профиль для редактирования',
)
async def get_my_profile(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MyProfileResponse:
    counts = await GetUserProfileCountsService(db).execute(user.id)
    return build_my_profile_response(user, counts)


@router.patch(
    '/profile',
    response_model=MyProfileResponse,
    summary='Обновить поля своего профиля',
)
async def patch_my_profile(
    body: ProfileUpdateRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MyProfileResponse:
    patch = body.model_dump(exclude_unset=True)
    if not patch:
        counts = await GetUserProfileCountsService(db).execute(user.id)
        return build_my_profile_response(user, counts)

    try:
        updated = await UpdateMyProfileService(db).execute(user.id, patch)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    counts = await GetUserProfileCountsService(db).execute(updated.id)
    return build_my_profile_response(updated, counts)


@router.post(
    '/watchlist',
    response_model=WatchlistEntryItemResponse,
    status_code=201,
    summary='Добавить тему в список «Позже»',
)
async def post_my_watchlist_entry(
    body: WatchlistFilmCreateRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WatchlistEntryItemResponse:
    created_at = dt.datetime.now(dt.UTC)
    watch_tag = body.watch_tag.value
    watchlist_opts = {
        'company': body.company,
        'category_id': body.category_id,
        'watch_note': body.watch_note,
        'watch_with_user_id': body.watch_with_user_id,
        'watch_with_user_ids': body.watch_with_user_ids,
    }
    try:
        if body.film_id is not None:
            result = await CreateWatchlistEntryFromFilmService.build(db).execute(
                actor_user_id=user.id,
                film_id=body.film_id,
                watch_tag=watch_tag,
                created_at=created_at,
                **watchlist_opts,
            )
            entry_id = int(result.entry.actor_entry.id)
        elif body.catalog_item_id is not None:
            result = await CreateWatchlistEntryFromCatalogService.build(db).execute(
                actor_user_id=user.id,
                catalog_item_id=body.catalog_item_id,
                watch_tag=watch_tag,
                created_at=created_at,
                **watchlist_opts,
            )
            entry_id = int(result.entry.actor_entry.id)
        elif body.card_id is not None and body.provider_meta is not None:
            result = await CreateWatchlistEntryService.build(db).execute(
                actor_user_id=user.id,
                card_id=body.card_id,
                provider_meta=body.provider_meta,
                watch_tag=watch_tag,
                created_at=created_at,
                **watchlist_opts,
            )
            entry_id = int(result.actor_entry.id)
        else:
            raise HTTPException(
                status_code=422,
                detail='provide film_id, catalog_item_id, or card_id with provider_meta',
            )
    except CreateWatchlistEntryFromFilmService.FilmNotFoundError:
        raise HTTPException(status_code=404, detail='film not found') from None
    except CreateWatchlistEntryFromCatalogService.CatalogItemNotFoundError:
        raise HTTPException(status_code=404, detail='catalog item not found') from None
    except (
        CreateWatchlistEntryFromFilmService.MovieAlreadyRatedForFilmError,
        CreateWatchlistEntryFromCatalogService.MovieAlreadyRatedForCatalogError,
    ):
        raise HTTPException(
            status_code=422,
            detail='movie card already exists for this film',
        ) from None
    except CreateWatchlistEntryService.WatchlistEntryAlreadyExistsError:
        raise HTTPException(status_code=409, detail='watchlist entry already exists') from None
    except CreateWatchlistEntryService.WatchWithUserNotFoundError:
        raise HTTPException(status_code=404, detail='watch with user not found') from None
    except CreateWatchlistEntryService.NotMutualWatchPartnerError:
        raise HTTPException(
            status_code=422, detail='watch with user is not a mutual friend'
        ) from None

    return await _hydrated_entry_response(db, user.id, entry_id)


@router.get(
    '/planned-card',
    response_model=PlannedUserCardResponse,
    summary='Planned card metadata for prefill when rating from «Позже»',
)
async def get_my_planned_card(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    card_id: str | None = Query(default=None, min_length=1, max_length=128),
    film_id: int | None = Query(default=None, ge=1),
    catalog_item_id: int | None = Query(default=None, ge=1),
) -> PlannedUserCardResponse:
    if card_id is None and film_id is None and catalog_item_id is None:
        raise HTTPException(
            status_code=422,
            detail='provide card_id, film_id, or catalog_item_id',
        )
    planned = await GetPlannedUserCardService.build(db).execute(
        user.id,
        card_id=card_id,
        film_id=film_id,
        catalog_item_id=catalog_item_id,
    )
    if planned is None:
        raise HTTPException(status_code=404, detail='planned card not found')
    return PlannedUserCardResponse(
        user_card_id=planned.user_card_id,
        company=planned.company,
        category_id=planned.category_id,
        watch_note=planned.watch_note,
    )


@router.get(
    '/watchlist/presence',
    response_model=WatchlistMembershipResponse,
    summary='Проверить наличие темы в моём списке «Позже» по card_id',
)
async def get_my_watchlist_presence(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    card_id: str = Query(..., min_length=1, max_length=128),
) -> WatchlistMembershipResponse:
    present = await GetMyWatchlistPresenceService.build(db).execute(user.id, card_id)
    return WatchlistMembershipResponse(in_watchlist=present)


@router.get(
    '/watchlist/films/{film_id}',
    response_model=WatchlistMembershipResponse,
    summary='Проверить, есть ли фильм в моём списке «Позже»',
)
async def get_my_watchlist_film_presence(
    film_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WatchlistMembershipResponse:
    film = await db.get(Film, film_id)
    if film is None:
        return WatchlistMembershipResponse(in_watchlist=False)
    card_id = watchlist_card_id_for_provider(CatalogProvider.kinopoisk, str(film.kinopoisk_id))
    present = await GetMyWatchlistPresenceService.build(db).execute(user.id, card_id)
    return WatchlistMembershipResponse(in_watchlist=present)


@router.delete(
    '/watchlist/{entry_id}',
    status_code=204,
    response_class=Response,
    summary='Удалить запись из списка «Позже» по entry_id',
)
async def delete_my_watchlist_entry(
    entry_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    try:
        await DeleteWatchlistEntryService.build(db).execute_by_entry_id(user.id, entry_id)
    except DeleteWatchlistEntryService.WatchlistEntryNotFoundError:
        raise HTTPException(status_code=404, detail='watchlist entry not found') from None
    return Response(status_code=204)


@router.delete(
    '/watchlist/films/{film_id}',
    status_code=204,
    response_class=Response,
    summary='Убрать фильм из списка «Позже»',
)
async def delete_my_watchlist_film(
    film_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    try:
        await DeleteWatchlistEntryService.build(db).execute_by_film_id(user.id, film_id)
    except DeleteWatchlistEntryService.WatchlistEntryNotFoundError:
        raise HTTPException(status_code=404, detail='watchlist entry not found') from None
    return Response(status_code=204)


@router.post(
    '/cards/export-csv',
    response_model=UserCardsExportCsvResponse,
    summary='Отправить CSV со всеми своими карточками в Telegram',
)
async def post_export_my_movie_cards_csv(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserCardsExportCsvResponse:
    svc = ExportMyUserCardsCsvTelegramService.build(db)
    try:
        await svc.execute(user)
    except SendTelegramBotMessageService.TelegramChatUnavailable:
        raise HTTPException(
            status_code=422,
            detail={
                'code': 'telegram_chat_unavailable',
                'message': (
                    'Чтобы получать уведомления, откройте бота в Telegram '
                    'и нажмите «Start» / «Запустить», затем попробуйте снова.'
                ),
                'bot_username': settings.telegram.bot_username,
            },
        ) from None
    except SendTelegramBotMessageService.TelegramDeliveryFailed as e:
        raise HTTPException(
            status_code=502,
            detail={
                'code': 'telegram_delivery_failed',
                'message': 'Не удалось связаться с Telegram. Попробуйте позже.',
            },
        ) from e

    return UserCardsExportCsvResponse(status='sent')
