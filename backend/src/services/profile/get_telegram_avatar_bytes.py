"""Stream the current Telegram profile photo without exposing the bot token."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from conf import settings
from integrations.telegram.bot_api_client import TelegramBotApiClient
from models.user import User
from services.profile.resolve_telegram_avatar_url import profile_photo_file_id
from utils.avatar_photo_url import sniff_image_content_type

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class TelegramAvatarBytes:
    body: bytes
    content_type: str


@dataclass
class GetTelegramAvatarBytesService:
    """Downloads the Telegram profile photo for a user who has no username.

    The public route stores this proxy path in ``photo_url`` after a custom avatar
    is removed. The next Telegram login replaces it with the CDN url from initData.
    """

    _session: AsyncSession
    _bot: TelegramBotApiClient | None

    class NotFound(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        token = settings.telegram.bot_token.strip()
        bot = TelegramBotApiClient(token) if token != '' else None
        return cls(_session=session, _bot=bot)

    async def execute(self, user_id: UUID) -> TelegramAvatarBytes:
        result = await self._session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None or self._bot is None:
            raise self.NotFound
        try:
            listed = await self._bot.get_user_profile_photos(user.telegram_user_id)
        except OSError as exc:
            logger.warning('telegram profile photo list failed user_id=%s', user_id)
            raise self.NotFound from exc
        file_id = profile_photo_file_id(listed.payload) if listed.ok else None
        if file_id is None:
            raise self.NotFound
        try:
            described = await self._bot.get_file(file_id)
        except OSError as exc:
            logger.warning('telegram getFile failed user_id=%s', user_id)
            raise self.NotFound from exc
        file_path = _file_path(described.payload) if described.ok else None
        if file_path is None:
            raise self.NotFound
        try:
            body = await self._bot.download_file(file_path)
        except OSError as exc:
            logger.warning('telegram file download failed user_id=%s', user_id)
            raise self.NotFound from exc
        if body is None:
            raise self.NotFound
        content_type = sniff_image_content_type(body)
        if content_type is None:
            raise self.NotFound
        return TelegramAvatarBytes(body=body, content_type=content_type)


def _file_path(payload: dict[str, object]) -> str | None:
    result = payload.get('result')
    if not isinstance(result, dict):
        return None
    raw = result.get('file_path')
    if not isinstance(raw, str):
        return None
    path = raw.strip().lstrip('/')
    if path == '' or '..' in path.split('/'):
        return None
    return path
