import pytest
from httpx import AsyncClient

from conf import settings
from tests.auth.telegram_init_data import build_init_data
from tests.auth.telegram_login_widget import build_login_widget_fields


@pytest.mark.asyncio
async def test_auth_telegram_widget_ok_sets_cookie_and_me(async_client: AsyncClient) -> None:
    payload = build_login_widget_fields(
        bot_token=settings.telegram.bot_token,
        user_id=55,
        username='widget_user',
    )
    r = await async_client.post('/api/auth/telegram-widget', json=payload)
    assert r.status_code == 200
    data = r.json()
    assert data['telegram_user_id'] == 55
    assert data['username'] == 'widget_user'
    assert data.get('access_token')
    assert settings.auth_jwt.session_cookie_name in r.cookies

    async_client.cookies.clear()
    me = await async_client.get(
        '/api/me',
        headers={'Authorization': f'Bearer {data["access_token"]}'},
    )
    assert me.status_code == 200
    assert me.json()['id'] == data['id']


@pytest.mark.asyncio
async def test_auth_telegram_widget_rejects_bad_hash(async_client: AsyncClient) -> None:
    payload = build_login_widget_fields(
        bot_token=settings.telegram.bot_token,
        user_id=56,
    )
    payload['hash'] = 'deadbeef'
    r = await async_client.post('/api/auth/telegram-widget', json=payload)
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_auth_telegram_widget_rejects_missing_hash(async_client: AsyncClient) -> None:
    payload = build_login_widget_fields(
        bot_token=settings.telegram.bot_token,
        user_id=57,
    )
    del payload['hash']
    r = await async_client.post('/api/auth/telegram-widget', json=payload)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_auth_telegram_widget_and_init_data_same_user(async_client: AsyncClient) -> None:
    user_id = 58
    widget_payload = build_login_widget_fields(
        bot_token=settings.telegram.bot_token,
        user_id=user_id,
        username='same_user',
    )
    r1 = await async_client.post('/api/auth/telegram-widget', json=widget_payload)
    assert r1.status_code == 200

    init = build_init_data(
        bot_token=settings.telegram.bot_token,
        user_id=user_id,
        username='same_user',
    )
    r2 = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert r2.status_code == 200
    assert r1.json()['id'] == r2.json()['id']
