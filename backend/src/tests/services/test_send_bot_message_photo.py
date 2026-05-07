"""send_photo: сначала multipart после скачивания URL, затем запасной sendPhoto по строке URL."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from integrations.telegram.bot_api_client import TelegramSendMessageResult
from services.telegram.send_bot_message import (
    SendTelegramBotMessageService,
    _sniff_image_content_type,
)


def test_sniff_image_content_type() -> None:
    assert _sniff_image_content_type(b'\xff\xd8\xff\xe0' + b'\x00' * 20) == 'image/jpeg'
    assert _sniff_image_content_type(b'<html><body') is None


@pytest.mark.asyncio
async def test_send_photo_uses_multipart_when_download_succeeds() -> None:
    client = AsyncMock()
    client.send_photo_multipart = AsyncMock(
        return_value=TelegramSendMessageResult(ok=True, payload={'ok': True})
    )
    client.send_photo = AsyncMock()
    svc = SendTelegramBotMessageService(_client=client)

    with patch(
        'services.telegram.send_bot_message._download_poster_bytes',
        new_callable=AsyncMock,
        return_value=(b'\xff\xd8\xff\xe0', 'kp.jpg', 'image/jpeg'),
    ):
        await svc.send_photo(42, 'https://example.com/kp.jpg', '<b>hi</b>', parse_mode='HTML')

    client.send_photo_multipart.assert_awaited_once()
    client.send_photo.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_photo_falls_back_to_url_when_download_returns_none() -> None:
    client = AsyncMock()
    client.send_photo = AsyncMock(
        return_value=TelegramSendMessageResult(ok=True, payload={'ok': True})
    )
    client.send_photo_multipart = AsyncMock()
    svc = SendTelegramBotMessageService(_client=client)

    with patch(
        'services.telegram.send_bot_message._download_poster_bytes',
        new_callable=AsyncMock,
        return_value=None,
    ):
        await svc.send_photo(7, 'https://example.com/x.jpg', 'cap')

    client.send_photo_multipart.assert_not_awaited()
    client.send_photo.assert_awaited_once_with(
        7, 'https://example.com/x.jpg', 'cap', parse_mode='HTML'
    )


@pytest.mark.asyncio
async def test_send_photo_falls_back_to_url_when_multipart_not_ok() -> None:
    client = AsyncMock()
    client.send_photo_multipart = AsyncMock(
        return_value=TelegramSendMessageResult(
            ok=False,
            payload={'ok': False, 'description': 'something'},
        )
    )
    client.send_photo = AsyncMock(
        return_value=TelegramSendMessageResult(ok=True, payload={'ok': True})
    )
    svc = SendTelegramBotMessageService(_client=client)

    with patch(
        'services.telegram.send_bot_message._download_poster_bytes',
        new_callable=AsyncMock,
        return_value=(b'data', 'a.jpg', 'image/jpeg'),
    ):
        await svc.send_photo(1, 'https://h/a.jpg', 'c')

    client.send_photo_multipart.assert_awaited_once()
    client.send_photo.assert_awaited_once()
