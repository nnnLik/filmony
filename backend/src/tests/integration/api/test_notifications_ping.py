"""Tests for POST /api/me/notifications/ping — mocked Telegram Bot API."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

from conf import settings
from integrations.telegram.bot_api_client import TelegramBotApiClient, TelegramSendMessageResult
from tests.auth.telegram_init_data import build_init_data


@pytest.fixture
async def logged_in_client(async_client: AsyncClient) -> AsyncClient:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=991_001)
    login = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert login.status_code == 200
    return async_client


async def test_notification_ping_sent(logged_in_client: AsyncClient) -> None:
    with patch.object(TelegramBotApiClient, 'send_message', new_callable=AsyncMock) as m:
        m.return_value = TelegramSendMessageResult(ok=True, payload={'ok': True, 'result': {}})
        r = await logged_in_client.post('/api/me/notifications/ping')

    assert r.status_code == 200
    assert r.json() == {'status': 'sent'}
    assert m.await_count == 1


async def test_notification_ping_chat_unavailable(logged_in_client: AsyncClient) -> None:
    with patch.object(TelegramBotApiClient, 'send_message', new_callable=AsyncMock) as m:
        m.return_value = TelegramSendMessageResult(
            ok=False,
            payload={
                'ok': False,
                'error_code': 403,
                'description': "Forbidden: bot can't initiate conversation with the user",
            },
        )
        r = await logged_in_client.post('/api/me/notifications/ping')

    assert r.status_code == 422
    detail = r.json()['detail']
    assert detail['code'] == 'telegram_chat_unavailable'
    assert 'bot_username' in detail


async def test_notification_ping_telegram_other_error(logged_in_client: AsyncClient) -> None:
    with patch.object(TelegramBotApiClient, 'send_message', new_callable=AsyncMock) as m:
        m.return_value = TelegramSendMessageResult(
            ok=False,
            payload={'ok': False, 'error_code': 500, 'description': 'internal telegram glitch'},
        )
        r = await logged_in_client.post('/api/me/notifications/ping')

    assert r.status_code == 502
    assert r.json()['detail']['code'] == 'telegram_delivery_failed'
