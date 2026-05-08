from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.profile.schemas import (
    MovieCardsExportCsvResponse,
    MyProfileResponse,
    ProfileUpdateRequest,
    WatchlistFilmAddRequest,
    WatchlistFilmItemResponse,
    WatchlistMembershipResponse,
    build_my_profile_response,
)
from conf import settings
from core.database import get_db
from deps.auth import CurrentUser
from services.profile.export_my_movie_cards_csv_telegram import ExportMyMovieCardsCsvTelegramService
from services.profile.get_user_profile_counts import GetUserProfileCountsService
from services.profile.update_my_profile import UpdateMyProfileService
from services.telegram.send_bot_message import SendTelegramBotMessageService
from services.watchlist.add_user_watchlist_film import AddUserWatchlistFilmService
from services.watchlist.get_my_watchlist_film_presence import GetMyWatchlistFilmPresenceService
from services.watchlist.remove_user_watchlist_film import RemoveUserWatchlistFilmService

router = APIRouter(prefix='/me', tags=['profile'])


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
    response_model=MovieCardsExportCsvResponse,
    summary='Отправить CSV со всеми своими карточками в Telegram',
)
async def post_export_my_movie_cards_csv(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MovieCardsExportCsvResponse:
    svc = ExportMyMovieCardsCsvTelegramService.build(db)
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

    return MovieCardsExportCsvResponse(status='sent')


@router.post(
    '/watchlist',
    response_model=WatchlistFilmItemResponse,
    summary='Добавить фильм в список «к просмотру»',
)
async def post_my_watchlist_film(
    body: WatchlistFilmAddRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WatchlistFilmItemResponse:
    svc = AddUserWatchlistFilmService(db)
    try:
        item = await svc.execute(user.id, body.film_id)
    except svc.FilmNotFoundError:
        raise HTTPException(status_code=404, detail='film not found') from None
    except svc.MovieAlreadyRatedForFilmError:
        raise HTTPException(
            status_code=422,
            detail='movie card already exists for this film',
        ) from None
    except svc.WatchlistFilmAlreadyListedError:
        raise HTTPException(
            status_code=409,
            detail='film already in watchlist',
        ) from None
    return WatchlistFilmItemResponse(
        film_id=item.film_id,
        film_kinopoisk_id=item.film_kinopoisk_id,
        film_genres=item.film_genres,
        film_title=item.film_title,
        film_year=item.film_year,
        film_poster_url=item.film_poster_url,
    )


@router.get(
    '/watchlist/films/{film_id}',
    response_model=WatchlistMembershipResponse,
    summary='Проверить, есть ли фильм в моём списке «к просмотру»',
)
async def get_my_watchlist_film_presence(
    film_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WatchlistMembershipResponse:
    present = await GetMyWatchlistFilmPresenceService(db).execute(user.id, film_id)
    return WatchlistMembershipResponse(in_watchlist=present)


@router.delete(
    '/watchlist/films/{film_id}',
    status_code=204,
    response_class=Response,
    summary='Убрать фильм из списка «к просмотру»',
)
async def delete_my_watchlist_film(
    film_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    svc = RemoveUserWatchlistFilmService(db)
    try:
        await svc.execute(user.id, film_id)
    except svc.WatchlistEntryNotFoundError:
        raise HTTPException(status_code=404, detail='watchlist entry not found') from None
    return Response(status_code=204)
