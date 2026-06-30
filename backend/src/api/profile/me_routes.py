from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.profile.schemas import (
    MyProfileResponse,
    MyUserCardCategoryCreateRequest,
    MyUserCardCategoryListResponse,
    MyUserCardCategoryRenameRequest,
    MyUserCardCategoryResponse,
    MyUserCardTagStatItem,
    MyUserCardTagStatsResponse,
    ProfileUpdateRequest,
    UserCardsExportCsvResponse,
    build_my_profile_response,
)
from conf import settings
from core.database import get_db
from deps.auth import CurrentUser
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

router = APIRouter(prefix='/me', tags=['profile'])


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


