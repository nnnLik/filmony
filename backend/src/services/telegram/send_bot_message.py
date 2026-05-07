"""Send a plain-text DM via Telegram Bot API."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from conf import settings
from integrations.telegram.bot_api_client import TelegramBotApiClient


def _telegram_chat_unavailable(payload: dict[str, object]) -> bool:
    if payload.get('ok'):
        return False
    desc = str(payload.get('description') or '').lower()
    code = int(payload.get('error_code') or 0)
    if code == 400 and ('chat not found' in desc or 'peer_id_invalid' in desc):
        return True
    if code != 403:
        return False
    markers = (
        "can't initiate conversation",
        'blocked by the user',
        'bot was blocked',
        'user is deactivated',
    )
    return any(m in desc for m in markers)


@dataclass
class SendTelegramBotMessageService:
    """Delivers a single outbound Bot API message to a user's Telegram chat.

    Product flows (friend requests, shared cards) will call this with the recipient's
    ``telegram_user_id`` so the bot can DM deep links back into the Mini App.
    """

    _client: TelegramBotApiClient

    class TelegramBotMessageError(Exception):
        pass

    class TelegramChatUnavailable(TelegramBotMessageError):
        """User has no DM thread with the bot (no /start), blocked the bot, etc."""

        def __init__(self) -> None:
            super().__init__('telegram chat unavailable')

    class TelegramDeliveryFailed(TelegramBotMessageError):
        pass

    @classmethod
    def build(cls) -> Self:
        return cls(_client=TelegramBotApiClient(settings.telegram.bot_token))

    async def execute(
        self,
        chat_id: int,
        text: str,
        *,
        parse_mode: str | None = None,
    ) -> None:
        try:
            result = await self._client.send_message(chat_id, text, parse_mode=parse_mode)
        except Exception as e:
            raise self.TelegramDeliveryFailed('telegram transport error') from e

        if result.ok:
            return

        payload = result.payload
        if _telegram_chat_unavailable(payload):
            raise self.TelegramChatUnavailable from None

        desc = str(payload.get('description') or 'telegram send failed')
        raise self.TelegramDeliveryFailed(desc)

    async def send_photo(
        self,
        chat_id: int,
        photo_url: str,
        caption: str,
        *,
        parse_mode: str | None = 'HTML',
    ) -> None:
        try:
            result = await self._client.send_photo(
                chat_id, photo_url, caption, parse_mode=parse_mode
            )
        except Exception as e:
            raise self.TelegramDeliveryFailed('telegram transport error') from e

        if result.ok:
            return

        payload = result.payload
        if _telegram_chat_unavailable(payload):
            raise self.TelegramChatUnavailable from None

        desc = str(payload.get('description') or 'telegram sendPhoto failed')
        raise self.TelegramDeliveryFailed(desc)
