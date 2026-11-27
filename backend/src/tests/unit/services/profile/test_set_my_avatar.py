"""Avatar upload rejects bad files before touching storage."""

from __future__ import annotations

from uuid import uuid4

import pytest

from services.profile.resolve_telegram_avatar_url import ResolveTelegramAvatarUrlService
from services.profile.set_my_avatar import SetMyAvatarService
from utils.avatar_photo_url import AVATAR_MAX_BYTES

JPEG = b'\xff\xd8\xff\xe0' + b'\x00' * 16
PNG = b'\x89PNG\r\n\x1a\n' + b'\x00' * 16


class _UnusedSession:
    async def execute(self, _statement: object) -> None:
        raise AssertionError('validation must fail before a database read')


def _service() -> SetMyAvatarService:
    return SetMyAvatarService(
        _session=_UnusedSession(),  # type: ignore[arg-type]
        _resolve_telegram_avatar=ResolveTelegramAvatarUrlService(_bot=None),
    )


@pytest.mark.asyncio
async def test_set_my_avatar_rejects_empty_file() -> None:
    with pytest.raises(SetMyAvatarService.AvatarValidationError, match='empty file'):
        await _service().execute(uuid4(), 'image/jpeg', b'')


@pytest.mark.asyncio
async def test_set_my_avatar_rejects_mismatched_signature() -> None:
    with pytest.raises(SetMyAvatarService.AvatarValidationError, match='unsupported image type'):
        await _service().execute(uuid4(), 'image/jpeg', PNG)


@pytest.mark.asyncio
async def test_set_my_avatar_rejects_non_image() -> None:
    with pytest.raises(SetMyAvatarService.AvatarValidationError, match='unsupported image type'):
        await _service().execute(uuid4(), 'text/plain', JPEG)


@pytest.mark.asyncio
async def test_set_my_avatar_rejects_file_over_limit() -> None:
    blob = b'\xff\xd8\xff' + b'\x00' * AVATAR_MAX_BYTES
    with pytest.raises(SetMyAvatarService.AvatarValidationError, match='file too large'):
        await _service().execute(uuid4(), 'image/jpeg', blob)
