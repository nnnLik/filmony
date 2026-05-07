"""HTML DM for engagement notifications (non-blocking on Telegram errors)."""

from __future__ import annotations

import logging

from services.telegram.send_bot_message import SendTelegramBotMessageService

logger = logging.getLogger(__name__)


async def deliver_engagement_html_message(chat_id: int, html_text: str) -> None:
    """Send one HTML message; swallow Telegram recipient errors."""
    send_svc = SendTelegramBotMessageService.build()
    try:
        await send_svc.execute(chat_id, html_text, parse_mode='HTML')
    except SendTelegramBotMessageService.TelegramChatUnavailable:
        logger.info('telegram engagement skipped (no chat) chat_id=%s', chat_id)
    except SendTelegramBotMessageService.TelegramDeliveryFailed as exc:
        logger.warning('telegram engagement delivery failed chat_id=%s err=%s', chat_id, exc)
