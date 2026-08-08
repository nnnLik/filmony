"""API tests for GET /api/me/recap routes."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from core.database import get_session_factory
from models.film import Film
from models.film_actor import FilmActor
from models.person import Person
from services.profile.build_monthly_recap import previous_complete_month
from tests.integration.api.test_profile_routes import _login, _seed_movie_card


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
        genres=['драма', 'фантастика'],
        countries=['США'],
        primary_director_kinopoisk_id=301,
        primary_director_name='Дени Вильнёв',
    )
    await _seed_movie_card(
        user_id=user_id,
        kinopoisk_id=5400102,
        title='July Film B',
        year=1998,
        rating=7.5,
        company='alone',
        mood_after='enjoyed',
        tags=['recap'],
        completed_at=completed_at,
        genres=['драма'],
        countries=['Франция'],
        primary_director_kinopoisk_id=301,
        primary_director_name='Дени Вильнёв',
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
    assert body['top_director_name'] == 'Дени Вильнёв'
    assert body['top_director_count'] == 2
    assert body['top_director_kinopoisk_id'] == 301
    assert body['top_country_count'] == 1
    assert body['top_country'] in {'США', 'Франция'}
    assert body['genre_of_month'] == 'драма'
    assert len(body['genre_breakdown']) >= 2
    assert len(body['decade_breakdown']) == 2
    assert body['new_countries_count'] == 2
    assert len(body['director_breakdown']) >= 1
    assert body['director_breakdown'][0]['label'] == 'Дени Вильнёв'
    assert body['director_breakdown'][0]['count'] == 2


@pytest.mark.asyncio
async def test_get_my_monthly_recap_extended_fields_with_actor(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=54006)
    user_id = UUID(str(me['id']))
    completed_at = datetime(2026, 7, 18, 12, 0, tzinfo=UTC)

    await _seed_movie_card(
        user_id=user_id,
        kinopoisk_id=5400601,
        title='Actor Film',
        year=2023,
        rating=9.5,
        company='friends',
        mood_after='enjoyed',
        tags=[],
        completed_at=completed_at,
        genres=['драма'],
        countries=['США'],
        primary_director_kinopoisk_id=302,
        primary_director_name='Кристофер Нолан',
    )

    session_factory = get_session_factory()
    async with session_factory() as session:
        film = (
            await session.execute(select(Film).where(Film.kinopoisk_id == 5400601))
        ).scalar_one()
        person = Person(kinopoisk_id=54006, name='Леонардо ДиКаприо', poster_url=None)
        session.add(person)
        await session.flush()
        session.add(FilmActor(film_id=film.id, person_id=person.id, billing_order=1))
        await session.commit()

    await _login(async_client, telegram_user_id=54006)
    r = await async_client.get('/api/me/recap/2026/7')
    assert r.status_code == 200
    body = r.json()
    assert body['top_actor_name'] == 'Леонардо ДиКаприо'
    assert body['top_actor_count'] == 1
    assert body['top_actor_kinopoisk_id'] == 54006
    assert len(body['actor_breakdown']) == 1
    assert body['dominant_mood_after'] == 'enjoyed'
    assert body['dominant_company'] == 'friends'
    assert body['streak_best_in_period'] == 1
    assert isinstance(body['fun_facts'], list)
    assert len(body['fun_facts']) >= 1
    assert any('драма' in fact for fact in body['fun_facts'])


@pytest.mark.asyncio
async def test_get_my_monthly_digest_aliases_recap(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=54007)
    user_id = UUID(str(me['id']))
    completed_at = datetime(2026, 7, 12, 12, 0, tzinfo=UTC)

    await _seed_movie_card(
        user_id=user_id,
        kinopoisk_id=5400701,
        title='Digest alias film',
        year=2022,
        rating=8.0,
        company='alone',
        mood_after='enjoyed',
        tags=[],
        completed_at=completed_at,
    )

    await _login(async_client, telegram_user_id=54007)
    recap = await async_client.get('/api/me/recap/2026/7')
    digest = await async_client.get('/api/me/digest/month/2026/7')
    assert recap.status_code == 200
    assert digest.status_code == 200
    assert recap.json() == digest.json()


@pytest.mark.asyncio
async def test_get_my_monthly_recap_franchise_breakdown(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=54005)
    user_id = UUID(str(me['id']))
    completed_at = datetime(2026, 7, 20, 12, 0, tzinfo=UTC)
    franchise_key = 'kp_franchise:301'

    await _seed_movie_card(
        user_id=user_id,
        kinopoisk_id=5400501,
        title='Matrix',
        year=1999,
        rating=9.0,
        company='alone',
        mood_after='enjoyed',
        tags=[],
        completed_at=completed_at,
        franchise_key=franchise_key,
    )
    await _seed_movie_card(
        user_id=user_id,
        kinopoisk_id=5400502,
        title='Matrix Reloaded',
        year=2003,
        rating=8.0,
        company='alone',
        mood_after='enjoyed',
        tags=[],
        completed_at=completed_at,
        franchise_key=franchise_key,
    )

    await _login(async_client, telegram_user_id=54005)
    r = await async_client.get('/api/me/recap/2026/7')
    assert r.status_code == 200
    body = r.json()
    assert len(body['franchise_breakdown']) == 1
    assert body['franchise_breakdown'][0]['franchise_key'] == franchise_key
    assert body['franchise_breakdown'][0]['count'] == 2
    assert body['franchise_breakdown'][0]['label'] == 'Matrix'


@pytest.mark.asyncio
async def test_get_my_monthly_recap_new_countries_excludes_prior(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=54004)
    user_id = UUID(str(me['id']))
    prior_at = datetime(2026, 6, 10, 12, 0, tzinfo=UTC)
    month_at = datetime(2026, 7, 15, 12, 0, tzinfo=UTC)

    await _seed_movie_card(
        user_id=user_id,
        kinopoisk_id=5400401,
        title='Prior US film',
        year=2020,
        rating=8.0,
        company='alone',
        mood_after='enjoyed',
        tags=[],
        completed_at=prior_at,
        countries=['США'],
    )
    await _seed_movie_card(
        user_id=user_id,
        kinopoisk_id=5400402,
        title='July JP film',
        year=2021,
        rating=9.0,
        company='alone',
        mood_after='enjoyed',
        tags=[],
        completed_at=month_at,
        countries=['Япония'],
    )

    await _login(async_client, telegram_user_id=54004)
    r = await async_client.get('/api/me/recap/2026/7')
    assert r.status_code == 200
    body = r.json()
    assert body['new_countries_count'] == 1
    assert body['top_country'] == 'Япония'


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
