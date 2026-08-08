"""Integration tests for weekly personal digest builder and API."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
from httpx import AsyncClient

from core.database import get_session_factory
from services.personal_digest.build_personal_digest import BuildPersonalDigestService
from services.personal_digest.week_bounds import (
    previous_complete_iso_week,
    week_bounds_for_iso_week,
)
from tests.integration.api.test_profile_routes import _login, _seed_movie_card


@pytest.mark.asyncio
async def test_build_weekly_digest_happy_path(prepare_db: None) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        from models.user import User

        user = User(telegram_user_id=9_820_001, profile_slug='weekly-digest-user')
        session.add(user)
        await session.commit()
        user_id = user.id

    completed_at = datetime(2026, 7, 15, 12, 0, tzinfo=UTC)
    await _seed_movie_card(
        user_id=user_id,
        kinopoisk_id=9_820_101,
        title='Week Film',
        year=2024,
        rating=9.0,
        company='alone',
        mood_after='enjoyed',
        tags=[],
        completed_at=completed_at,
        genres=['драма'],
        countries=['США'],
        primary_director_kinopoisk_id=301,
        primary_director_name='Дени Вильнёв',
    )

    async with session_factory() as session:
        digest = await BuildPersonalDigestService.build(session).execute(
            user_id,
            period='week',
            period_key='2026-W29',
        )

    assert digest.period == 'week'
    assert digest.period_key == '2026-W29'
    assert digest.total_rated == 1
    assert digest.top_films[0].title == 'Week Film'
    assert digest.top_director_name == 'Дени Вильнёв'


@pytest.mark.asyncio
async def test_get_my_weekly_digest_route(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=9_820_002)
    user_id = UUID(str(me['id']))
    completed_at = datetime(2026, 7, 16, 12, 0, tzinfo=UTC)

    await _seed_movie_card(
        user_id=user_id,
        kinopoisk_id=9_820_201,
        title='API Week Film',
        year=2023,
        rating=8.0,
        company='alone',
        mood_after='enjoyed',
        tags=[],
        completed_at=completed_at,
        genres=['триллер'],
        countries=['Франция'],
        primary_director_kinopoisk_id=302,
        primary_director_name='Кристофер Нолан',
    )

    await _login(async_client, telegram_user_id=9_820_002)
    response = await async_client.get('/api/me/digest/week/2026-W29')
    assert response.status_code == 200
    body = response.json()
    assert body['period'] == 'week'
    assert body['period_key'] == '2026-W29'
    assert body['total_rated'] == 1
    assert body['top_films'][0]['title'] == 'API Week Film'


@pytest.mark.asyncio
async def test_get_my_latest_weekly_digest_route(async_client: AsyncClient) -> None:
    period_key, iso_year, iso_week = previous_complete_iso_week()
    week_start, _ = week_bounds_for_iso_week(iso_year=iso_year, iso_week=iso_week)

    me = await _login(async_client, telegram_user_id=9_820_003)
    user_id = UUID(str(me['id']))
    completed_at = week_start + timedelta(hours=12)

    await _seed_movie_card(
        user_id=user_id,
        kinopoisk_id=9_820_301,
        title='Latest Week Film',
        year=2022,
        rating=7.5,
        company='alone',
        mood_after='enjoyed',
        tags=[],
        completed_at=completed_at,
        genres=['драма'],
        countries=['США'],
        primary_director_kinopoisk_id=303,
        primary_director_name='Спайк Ли',
    )

    await _login(async_client, telegram_user_id=9_820_003)
    response = await async_client.get('/api/me/digest/week/latest')
    assert response.status_code == 200
    body = response.json()
    assert body['period'] == 'week'
    assert body['period_key'] == period_key
    assert body['total_rated'] == 1
