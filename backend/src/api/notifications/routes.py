from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from conf import settings
from deps.auth import CurrentUser
from services.telegram.send_bot_message import SendTelegramBotMessageService

router = APIRouter(prefix='/me/notifications', tags=['notifications'])

_PING_TEXT = 'Filmony: тестовое уведомление. Если вы это видите — чат с ботом готов.'


class NotificationPingResponse(BaseModel):
    status: str = Field(examples=['sent'])


@router.post(
    '/ping',
    response_model=NotificationPingResponse,
    summary='Отправить себе тестовое сообщение в Telegram',
)
async def post_notification_ping(user: CurrentUser) -> NotificationPingResponse:
    svc = SendTelegramBotMessageService.build()
    try:
        await svc.execute(chat_id=user.telegram_user_id, text=_PING_TEXT)
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

    return NotificationPingResponse(status='sent')
