"""Send a plain-text DM via Telegram Bot API."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Self
from urllib.parse import urlparse

import httpx

from conf import settings
from integrations.telegram.bot_api_client import TelegramBotApiClient, TelegramSendMessageResult

logger = logging.getLogger(__name__)

_MAX_TELEGRAM_PHOTO_BYTES = 10 * 1024 * 1024

# Некоторые CDN отдают постеры только «браузерному» UA; Telegram при URL-sendPhoto ходит со своего IP.
_POSTER_FETCH_USER_AGENT = (
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) '
    'Chrome/122.0.0.0 Safari/537.36'
)


def _sniff_image_content_type(body: bytes) -> str | None:
    """Определяет тип изображения по сигнатуре; отсекает HTML/JSON с кодом 200."""
    if len(body) < 12:
        return None
    if body.startswith(b'\xff\xd8\xff'):
        return 'image/jpeg'
    if body.startswith(b'\x89PNG\r\n\x1a\n'):
        return 'image/png'
    if body.startswith((b'GIF87a', b'GIF89a')):
        return 'image/gif'
    if body.startswith(b'RIFF') and body[8:12] == b'WEBP':
        return 'image/webp'
    return None


def _safe_photo_filename(url_path_tail: str) -> str:
    base = url_path_tail.strip() or 'poster.jpg'
    if len(base) > 120:
        base = 'poster.jpg'
    if not re.fullmatch(r'[A-Za-z0-9._-]+', base):
        return 'poster.jpg'
    return base


async def _download_poster_bytes(url: str) -> tuple[bytes, str, str] | None:
    """Скачивает постер для отправки в Telegram multipart (обход ограничений URL у Bot API)."""
    host = urlparse(url).netloc
    try:
        async with httpx.AsyncClient(timeout=35.0, follow_redirects=True) as client:
            response = await client.get(
                url,
                headers={
                    'User-Agent': _POSTER_FETCH_USER_AGENT,
                    'Accept': 'image/avif,image/webp,image/apng,image/*,*/*;q=0.8',
                },
            )
    except Exception as exc:
        logger.warning('poster download failed host=%s err=%s', host, exc)
        return None
    if response.status_code != 200:
        logger.warning(
            'poster download bad status host=%s status=%s',
            host,
            response.status_code,
        )
        return None
    body = response.content
    if not body or len(body) > _MAX_TELEGRAM_PHOTO_BYTES:
        logger.warning(
            'poster download empty or too large host=%s bytes=%s',
            host,
            len(body) if body else 0,
        )
        return None
    sniffed = _sniff_image_content_type(body)
    if sniffed is None:
        head = body[:64]
        preview = head.decode('utf-8', errors='replace') if head.isascii() else head[:16].hex()
        logger.warning('poster download not image bytes host=%s head=%r', host, preview)
        return None
    path = urlparse(url).path.strip('/')
    raw_name = path.rsplit('/', 1)[-1] if path else 'poster.jpg'
    suffix_for_mime = {
        'image/jpeg': '.jpg',
        'image/png': '.png',
        'image/gif': '.gif',
        'image/webp': '.webp',
    }
    suffix = suffix_for_mime.get(sniffed, '.jpg')
    filename = _safe_photo_filename(raw_name)
    if not filename.lower().endswith(('.jpg', '.jpeg', '.png', '.gif', '.webp')):
        stem = filename.rsplit('.', 1)[0] if '.' in filename else filename
        filename = f'{stem}{suffix}' if stem else f'poster{suffix}'
    return body, filename, sniffed


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

    Product flows (friend requests, shared cards) call this with the recipient's
    ``telegram_user_id`` for outbound DMs.
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

    def _raise_for_telegram_result(
        self, result: TelegramSendMessageResult, *, default_err: str
    ) -> None:
        if result.ok:
            return
        payload = result.payload
        if _telegram_chat_unavailable(payload):
            raise self.TelegramChatUnavailable from None
        raise self.TelegramDeliveryFailed(str(payload.get('description') or default_err))

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

        self._raise_for_telegram_result(result, default_err='telegram send failed')

    async def send_photo(
        self,
        chat_id: int,
        photo_url: str,
        caption: str,
        *,
        parse_mode: str | None = 'HTML',
    ) -> None:
        downloaded = await _download_poster_bytes(photo_url)
        if downloaded is not None:
            photo_bytes, filename, content_type = downloaded
            try:
                mp = await self._client.send_photo_multipart(
                    chat_id,
                    photo_bytes,
                    caption,
                    filename=filename,
                    content_type=content_type,
                    parse_mode=parse_mode,
                )
            except Exception as e:
                raise self.TelegramDeliveryFailed('telegram transport error') from e
            if mp.ok:
                return
            if _telegram_chat_unavailable(mp.payload):
                raise self.TelegramChatUnavailable from None
            logger.warning(
                'telegram sendPhoto multipart failed chat_id=%s err=%s',
                chat_id,
                mp.payload.get('description'),
            )

        try:
            result = await self._client.send_photo(
                chat_id, photo_url, caption, parse_mode=parse_mode
            )
        except Exception as e:
            raise self.TelegramDeliveryFailed('telegram transport error') from e

        self._raise_for_telegram_result(result, default_err='telegram sendPhoto failed')
