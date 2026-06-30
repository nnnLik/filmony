from __future__ import annotations

import pytest
from httpx import AsyncClient

from conf import settings
from core.database import get_session_factory
from models.film import Film
from tests.auth.telegram_init_data import build_init_data


async def _login(async_client: AsyncClient, telegram_user_id: int) -> dict[str, object]:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    r = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert r.status_code == 200
    return r.json()


async def _create_film(*, kinopoisk_id: int = 700_111) -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title='Test Watchlist Film',
            year=2024,
            poster_url='https://example.com/watchlist.jpg',
            genres=['драма'],
        )
        session.add(film)
        await session.commit()
        await session.refresh(film)
        return film


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
async def test_create_watchlist_entry_from_film_id(
    async_client: AsyncClient,
) -> None:
    await _login(async_client, telegram_user_id=910120)
    film = await _create_film(kinopoisk_id=701_001)

    response = await async_client.post('/api/me/watchlist', json={'film_id': film.id})

    assert response.status_code == 201
    body = response.json()
    assert body['film_id'] == film.id
    assert body['film_kinopoisk_id'] == film.kinopoisk_id


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
