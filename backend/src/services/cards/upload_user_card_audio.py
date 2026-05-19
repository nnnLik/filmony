from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Self
from uuid import UUID, uuid4

from core.rustfs_s3_client import RustfsPutObjectError, RustfsS3Client
from utils.user_card_media_key import (
    USER_CARD_AUDIO_RUSTFS_KEY_PREFIX,
    USER_CARD_MEDIA_API_PATH_PREFIX,
)

_ALLOWED_CT_SUFFIX: dict[str, str] = {
    'audio/mpeg': '.mp3',
    'audio/mp4': '.m4a',
    'audio/ogg': '.ogg',
    'audio/wav': '.wav',
    'audio/webm': '.webm',
}

USER_CARD_AUDIO_MAX_BYTES = 50 * 1024 * 1024


class UserCardAudioUploadError(Exception):
    """Invalid type/size or storage not configured."""


@dataclass
class UploadUserCardAudioService:
    """Writes one validated audio file for a user card to RustFS and returns the API proxy path."""

    @classmethod
    def build(cls) -> Self:
        return cls()

    async def execute(
        self,
        *,
        user_id: UUID,
        content_type: str,
        data: bytes,
    ) -> str:
        ct = content_type.strip().lower()
        if ct not in _ALLOWED_CT_SUFFIX:
            raise UserCardAudioUploadError('unsupported audio type')
        if len(data) == 0:
            raise UserCardAudioUploadError('empty file')
        if len(data) > USER_CARD_AUDIO_MAX_BYTES:
            raise UserCardAudioUploadError('file too large')

        client = RustfsS3Client.try_build_from_settings()
        if client is None:
            raise UserCardAudioUploadError('storage not configured')

        ext = _ALLOWED_CT_SUFFIX[ct]
        key = f'{USER_CARD_AUDIO_RUSTFS_KEY_PREFIX}{user_id}/{uuid4().hex}{ext}'

        try:
            await asyncio.to_thread(client.put_object, key, data, ct)
        except RustfsPutObjectError as exc:
            raise UserCardAudioUploadError(str(exc)) from exc

        return f'{USER_CARD_MEDIA_API_PATH_PREFIX}{key}'
