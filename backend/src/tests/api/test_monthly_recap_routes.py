"""API tests for GET /api/me/recap routes."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from httpx import AsyncClient

from services.profile.build_monthly_recap import previous_complete_month
from tests.api.test_profile_routes import _login, _seed_movie_card


@pytest.mark.asyncio
async def test_get_my_monthly_recap_happy_path(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=54001)
    user_id = UUID(str(me['id']))
    completed_at = datetime(2026, 7, 15, 12, 0, tzinfo=UTC)

    await _seed_movie_card(
        user_id=user_id,
        kinopoisk_id=5400101,
        title='July Film A',
        year=2024,
        rating=9.0,
        company='alone',
        mood_after='enjoyed',
        tags=['recap'],
        completed_at=completed_at,
    )
    await _seed_movie_card(
        user_id=user_id,
        kinopoisk_id=5400102,
        title='July Film B',
        year=2023,
        rating=7.5,
        company='alone',
        mood_after='enjoyed',
        tags=['recap'],
        completed_at=completed_at,
    )

    await _login(async_client, telegram_user_id=54001)
    r = await async_client.get('/api/me/recap/2026/7')
    assert r.status_code == 200
    body = r.json()
    assert body['year'] == 2026
    assert body['month'] == 7
    assert body['total_rated'] == 2
    assert len(body['top_films']) == 2
    assert body['top_films'][0]['rating'] == 9.0


@pytest.mark.asyncio
async def test_get_my_monthly_recap_requires_auth(async_client: AsyncClient) -> None:
    r = await async_client.get('/api/me/recap/2026/7')
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_get_my_monthly_recap_not_found_when_empty(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=54002)
    r = await async_client.get('/api/me/recap/2020/1')
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_get_my_latest_monthly_recap(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=54003)
    user_id = UUID(str(me['id']))
    year, month = previous_complete_month(now=datetime(2026, 8, 4, tzinfo=UTC))
    completed_at = datetime(year, month, 10, 12, 0, tzinfo=UTC)

    await _seed_movie_card(
        user_id=user_id,
        kinopoisk_id=5400301,
        title='Latest recap film',
        year=2022,
        rating=8.0,
        company='alone',
        mood_after='enjoyed',
        tags=[],
        completed_at=completed_at,
    )

    await _login(async_client, telegram_user_id=54003)
    r = await async_client.get('/api/me/recap/latest')
    assert r.status_code == 200
    body = r.json()
    assert body['year'] == year
    assert body['month'] == month
    assert body['total_rated'] == 1
