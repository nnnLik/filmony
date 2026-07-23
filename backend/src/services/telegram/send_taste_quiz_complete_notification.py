"""Telegram notification when a guesser completes a taste quiz session."""

from __future__ import annotations

import html
import logging
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from core.database import disposable_async_session
from models.user import User
from services.telegram.mini_app_link import html_app_deep_link_block
from services.telegram.send_bot_message import SendTelegramBotMessageService

logger = logging.getLogger(__name__)


def _format_user_display(user: User) -> str:
    if user.display_name and user.display_name.strip():
        return user.display_name.strip()
    parts = [user.first_name or '', user.last_name or '']
    joined = ' '.join(p for p in parts if p).strip()
    if joined:
        return joined
    return user.profile_slug or 'Пользователь'


def _format_points(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return f'{value:.1f}'.replace('.', ',')


def _build_caption_html(*, guesser: User, round_points: float) -> str:
    guesser_safe = html.escape(_format_user_display(guesser))
    points_safe = html.escape(_format_points(round_points))
    deep = html_app_deep_link_block(link_text='Открыть Filmony')
    return (
        f'🎯 <b>{guesser_safe}</b> завершил(а) «Угадай вкус»\n\n'
        f'Очки за сессию: <b>{points_safe}</b> / 10\n\n'
        f'{deep}'
    )


@dataclass
class SendTasteQuizCompleteNotificationService:
    """Notifies the quiz owner in Telegram when a session completes."""

    @classmethod
    def build(cls) -> Self:
        return cls()

    async def execute(
        self,
        *,
        owner_user_id: UUID,
        guesser_user_id: UUID,
        round_points: float,
    ) -> None:
        async with disposable_async_session() as session:
            owner = await session.get(User, owner_user_id)
            guesser = await session.get(User, guesser_user_id)
            if owner is None or guesser is None or owner.telegram_user_id is None:
                return

            caption = _build_caption_html(guesser=guesser, round_points=round_points)
            chat_id = int(owner.telegram_user_id)
            send_svc = SendTelegramBotMessageService.build()
            try:
                await send_svc.execute(chat_id, caption, parse_mode='HTML')
            except SendTelegramBotMessageService.TelegramChatUnavailable:
                logger.info(
                    'taste quiz complete skipped (no chat) owner=%s guesser=%s',
                    owner_user_id,
                    guesser_user_id,
                )
            except SendTelegramBotMessageService.TelegramDeliveryFailed as exc:
                logger.warning(
                    'taste quiz complete delivery failed owner=%s err=%s',
                    owner_user_id,
                    exc,
                )


async def run_deliver_taste_quiz_complete_notification_safe(
    *,
    owner_user_id: UUID,
    guesser_user_id: UUID,
    round_points: float,
) -> None:
    try:
        await SendTasteQuizCompleteNotificationService.build().execute(
            owner_user_id=owner_user_id,
            guesser_user_id=guesser_user_id,
            round_points=round_points,
        )
    except Exception:
        logger.exception(
            'deliver taste quiz complete failed owner=%s guesser=%s',
            owner_user_id,
            guesser_user_id,
        )
