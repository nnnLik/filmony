from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.auth.schemas import TelegramAuthRequest, TelegramAuthResponse, UserResponse
from conf import settings
from core.database import get_db
from services.auth.errors import TelegramInitDataInvalidError
from services.auth.issue_session_jwt import IssueSessionJwtService
from services.auth.upsert_telegram_user import UpsertTelegramUserService
from services.auth.verify_telegram_init_data import VerifyTelegramInitDataService

router = APIRouter(prefix='/auth', tags=['auth'])


def _session_cookie_samesite() -> str:
    return 'none' if settings.app.is_prod else 'lax'


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=settings.auth_jwt.session_cookie_name,
        value=token,
        httponly=True,
        max_age=settings.auth_jwt.session_max_age_seconds,
        secure=settings.app.is_prod,
        samesite=_session_cookie_samesite(),
        path='/',
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=settings.auth_jwt.session_cookie_name,
        path='/',
        httponly=True,
        secure=settings.app.is_prod,
        samesite=_session_cookie_samesite(),
    )


@router.post('/telegram', response_model=TelegramAuthResponse)
async def auth_telegram(
    body: TelegramAuthRequest,
    response: Response,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TelegramAuthResponse:
    verifier = VerifyTelegramInitDataService(bot_token=settings.telegram.bot_token)
    try:
        profile = verifier.execute(body.init_data)
    except TelegramInitDataInvalidError:
        raise HTTPException(status_code=401, detail='invalid init data') from None

    user = await UpsertTelegramUserService(db).execute(profile)
    token = IssueSessionJwtService().execute(user.id)
    _set_session_cookie(response, token)
    base = UserResponse.model_validate(user)
    return TelegramAuthResponse(**base.model_dump(), access_token=token)


@router.post('/logout')
async def auth_logout(response: Response) -> dict[str, str]:
    _clear_session_cookie(response)
    return {'status': 'ok'}
