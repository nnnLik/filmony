from __future__ import annotations

import pytest
from httpx import AsyncClient

from conf import settings
from tests.auth.telegram_init_data import build_init_data


async def _login(async_client: AsyncClient, telegram_user_id: int) -> dict[str, object]:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    r = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert r.status_code == 200
    return r.json()


@pytest.mark.asyncio
async def test_create_watchlist_entry_with_provider_meta(
    async_client: AsyncClient,
) -> None:
    await _login(async_client, telegram_user_id=910100)
    payload = {
        'card_id': 'custom:concert-2026',
        'provider_meta': {'provider': 'custom', 'data': {'type': 'concert'}},
        'watch_tag': 'watch_later',
        'watch_with_user_id': None,
    }

    response = await async_client.post('/api/watchlist', json=payload)

    assert response.status_code == 201
    body = response.json()
    assert body['card_id'] == 'custom:concert-2026'
    assert body['provider_meta']['provider'] == 'custom'


@pytest.mark.asyncio
async def test_user_cannot_edit_other_watchlist_entry(
    async_client: AsyncClient,
) -> None:
    await _login(async_client, telegram_user_id=910110)
    payload = {
        'card_id': 'kp:123',
        'provider_meta': {'provider': 'kinopoisk', 'data': {'kp_id': 123}},
        'watch_tag': 'watch_later',
        'watch_with_user_id': None,
    }
    created = await async_client.post('/api/watchlist', json=payload)
    assert created.status_code == 201
    entry_id = created.json()['id']

    await _login(async_client, telegram_user_id=910111)
    response = await async_client.patch(
        f'/api/watchlist/{entry_id}',
        json={'watch_tag': 'watch_later'},
    )

    assert response.status_code == 403
