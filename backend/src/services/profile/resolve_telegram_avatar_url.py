"""Rebuild the Telegram avatar URL from username or the bot profile-photo API."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from conf import settings
from integrations.telegram.bot_api_client import TelegramBotApiClient
from utils.avatar_photo_url import telegram_avatar_proxy_path, telegram_userpic_url

logger = logging.getLogger(__name__)


def profile_photo_file_id(payload: dict[str, object]) -> str | None:
    result = payload.get('result')
    if not isinstance(result, dict):
        return None
    photos = result.get('photos')
    if not isinstance(photos, list) or not photos:
        return None
    sizes = photos[0]
    if not isinstance(sizes, list) or not sizes:
        return None
    best = sizes[-1]
    if not isinstance(best, dict):
        return None
    file_id = best.get('file_id')
    if isinstance(file_id, str) and file_id.strip() != '':
        return file_id
    return None


@dataclass
class ResolveTelegramAvatarUrlService:
    """Returns the Telegram avatar link to store when a custom avatar is removed.

    A username maps to the public ``t.me/i/userpic`` URL. Without a username the
    bot is asked whether a profile photo exists; the stored value is then our
    proxy path so the bot token never reaches the client. ``None`` means Telegram
    has no photo and the UI keeps showing initials.
    """

    _bot: TelegramBotApiClient | None

    @classmethod
    def build(cls) -> Self:
        token = settings.telegram.bot_token.strip()
        bot = TelegramBotApiClient(token) if token != '' else None
        return cls(_bot=bot)

    async def execute(
        self,
        *,
        user_id: UUID,
        telegram_user_id: int,
        username: str | None,
    ) -> str | None:
        cleaned = username.strip() if isinstance(username, str) else ''
        if cleaned != '':
            return telegram_userpic_url(cleaned)
        if self._bot is None:
            return None
        try:
            listed = await self._bot.get_user_profile_photos(telegram_user_id)
        except OSError:
            logger.warning('telegram profile photo lookup failed user_id=%s', user_id)
            return None
        if not listed.ok or profile_photo_file_id(listed.payload) is None:
            return None
        return telegram_avatar_proxy_path(user_id)
