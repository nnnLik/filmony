import time

import pytest
from httpx import AsyncClient

from conf import settings

from tests.auth.telegram_init_data import build_init_data


@pytest.mark.asyncio
async def test_auth_telegram_rejects_bad_hash(async_client: AsyncClient) -> None:
    bad = "auth_date=1&user=%7B%22id%22%3A1%7D&hash=deadbeef"
    r = await async_client.post("/api/auth/telegram", json={"initData": bad})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_auth_telegram_rejects_expired_auth_date(async_client: AsyncClient) -> None:
    old = int(time.time()) - 200_000
    init = build_init_data(
        bot_token=settings.telegram.bot_token,
        user_id=7,
        auth_date=old,
    )
    r = await async_client.post("/api/auth/telegram", json={"initData": init})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_auth_telegram_ok_sets_cookie_and_me(async_client: AsyncClient) -> None:
    init = build_init_data(
        bot_token=settings.telegram.bot_token,
        user_id=99,
        username="u99",
    )
    r = await async_client.post("/api/auth/telegram", json={"initData": init})
    assert r.status_code == 200
    data = r.json()
    assert data["telegram_user_id"] == 99
    assert data["username"] == "u99"
    assert settings.auth_jwt.session_cookie_name in r.cookies

    me = await async_client.get("/api/me")
    assert me.status_code == 200
    assert me.json()["id"] == data["id"]


@pytest.mark.asyncio
async def test_me_without_cookie(async_client: AsyncClient) -> None:
    r = await async_client.get("/api/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_auth_idempotent(async_client: AsyncClient) -> None:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=100)
    r1 = await async_client.post("/api/auth/telegram", json={"initData": init})
    r2 = await async_client.post("/api/auth/telegram", json={"initData": init})
    assert r1.status_code == 200 and r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"]


@pytest.mark.asyncio
async def test_logout(async_client: AsyncClient) -> None:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=101)
    r = await async_client.post("/api/auth/telegram", json={"initData": init})
    assert r.status_code == 200

    lo = await async_client.post("/api/auth/logout")
    assert lo.status_code == 200

    me = await async_client.get("/api/me")
    assert me.status_code == 401
