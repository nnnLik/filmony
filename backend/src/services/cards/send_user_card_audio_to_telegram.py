"""Loads card vibe audio from RustFS and sends it to the viewer's Telegram chat as a document."""

from __future__ import annotations

import asyncio
import re
from dataclasses import dataclass
from typing import Self

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from conf import settings
from core.rustfs_s3_client import (
    RustfsClientError,
    RustfsKeyNotFoundError,
    get_rustfs_object_bytes,
)
from models.user import User
from services.cards.get_user_card_details import GetUserCardDetailsService
from services.telegram.send_bot_message import SendTelegramBotMessageService
from utils.user_card_media_key import rustfs_key_from_user_card_audio_proxy_url

_CT_TO_EXT: dict[str, str] = {
    'audio/mpeg': '.mp3',
    'audio/mp4': '.m4a',
    'audio/ogg': '.ogg',
    'audio/wav': '.wav',
    'audio/webm': '.webm',
}

_MAX_TELEGRAM_DOCUMENT_BYTES = 50 * 1024 * 1024


class UserCardAudioTelegramError(Exception):
    """Base for send-audio-to-Telegram failures."""


class UserCardAudioMissingError(UserCardAudioTelegramError):
    """Card has no attached audio."""


class UserCardAudioKeyInvalidError(UserCardAudioTelegramError):
    """Stored proxy URL does not map to a RustFS key."""


class UserCardAudioStorageNotConfiguredError(UserCardAudioTelegramError):
    """RustFS / media settings incomplete."""


class UserCardAudioObjectNotFoundError(UserCardAudioTelegramError):
    """Object missing in bucket."""


class UserCardAudioFetchError(UserCardAudioTelegramError):
    """Upstream read failed."""


class UserCardAudioTooLargeError(UserCardAudioTelegramError):
    """File exceeds Telegram Bot document limit."""


async def load_user_card_audio_media_bytes(rustfs_key: str) -> tuple[bytes, str]:
    """Read bytes from RustFS (S3 API or plain HTTP), same strategy as ``GET /api/cards/media/...``."""
    internal = settings.reaction_media.rustfs_internal_base_url.strip().rstrip('/')
    if not internal:
        raise UserCardAudioStorageNotConfiguredError('media storage not configured')
    bucket = settings.reaction_media.rustfs_bucket.strip()
    safe_key = rustfs_key.lstrip('/')
    access = settings.reaction_media.rustfs_access_key.strip()
    secret = settings.reaction_media.rustfs_secret_key.strip()

    if access and secret:
        try:
            result = await asyncio.to_thread(
                get_rustfs_object_bytes,
                endpoint_url=internal,
                access_key_id=access,
                secret_access_key=secret,
                bucket=bucket,
                key=safe_key,
            )
        except RustfsKeyNotFoundError as e:
            raise UserCardAudioObjectNotFoundError(str(e)) from e
        except RustfsClientError as e:
            raise UserCardAudioFetchError(str(e)) from e
        ct = (
            result.content_type.strip()
            if isinstance(result.content_type, str) and result.content_type.strip()
            else 'application/octet-stream'
        )
        return result.body, ct

    url = f'{internal}/{bucket}/{safe_key}'
    timeout = httpx.Timeout(18.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            upstream = await client.get(url)
    except httpx.HTTPError as exc:
        raise UserCardAudioFetchError('storage unreachable') from exc
    if upstream.status_code != 200:
        raise UserCardAudioObjectNotFoundError('not found')
    ct_raw = upstream.headers.get('content-type')
    ct = ct_raw.strip() if isinstance(ct_raw, str) and ct_raw.strip() else 'application/octet-stream'
    return upstream.content, ct


def _extension_for_content_type(content_type: str) -> str:
    base = content_type.split(';', 1)[0].strip().lower()
    return _CT_TO_EXT.get(base, '.bin')


def _safe_document_filename(card_id: int, ext: str) -> str:
    e = ext if re.fullmatch(r'\.[a-z0-9]{2,5}', ext.lower()) else '.bin'
    return f'filmony-card-{card_id}-audio{e}'


@dataclass
class SendUserCardAudioToTelegramService:
    """Fetches card audio from RustFS and delivers it as a Telegram document to the viewer's bot chat."""

    _session: AsyncSession
    _telegram: SendTelegramBotMessageService

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session, _telegram=SendTelegramBotMessageService.build())

    async def execute(self, *, card_id: int, viewer: User) -> None:
        details = await GetUserCardDetailsService(self._session).execute(card_id, viewer.id)
        raw_url = (details.audio_url or '').strip()
        if raw_url == '':
            raise UserCardAudioMissingError('no audio on this card')

        key = rustfs_key_from_user_card_audio_proxy_url(raw_url)
        if key is None:
            raise UserCardAudioKeyInvalidError('invalid audio url')

        body, content_type = await load_user_card_audio_media_bytes(key)
        if len(body) > _MAX_TELEGRAM_DOCUMENT_BYTES:
            raise UserCardAudioTooLargeError('audio file too large for Telegram')

        ext = _extension_for_content_type(content_type)
        filename = _safe_document_filename(card_id, ext)
        title = (details.display_title or '').strip() or 'Карточка'
        caption = f'Аудио с карточки «{title}»'

        await self._telegram.send_document(
            chat_id=int(viewer.telegram_user_id),
            document_bytes=body,
            filename=filename,
            content_type=content_type.split(';', 1)[0].strip() or 'application/octet-stream',
            caption=caption,
        )
