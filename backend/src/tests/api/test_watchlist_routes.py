from __future__ import annotations

from uuid import uuid4

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


async def _create_film(*, kinopoisk_id: int, title: str = 'Фильм', year: int | None = 2020) -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title=title,
            year=year,
            poster_url=None,
            genres=['драма'],
        )
        session.add(film)
        await session.commit()
        await session.refresh(film)
        return film


@pytest.mark.asyncio
async def test_post_watchlist_requires_auth(async_client: AsyncClient) -> None:
    film = await _create_film(kinopoisk_id=910001)
    r = await async_client.post('/api/me/watchlist', json={'film_id': film.id})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_post_watchlist_success_and_list_public(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=910010)
    film = await _create_film(kinopoisk_id=910011, title='Списочный фильм')

    added = await async_client.post('/api/me/watchlist', json={'film_id': film.id})
    assert added.status_code == 200
    row = added.json()
    assert row['film_id'] == film.id
    assert row['film_title'] == 'Списочный фильм'

    presence = await async_client.get(f'/api/me/watchlist/films/{film.id}')
    assert presence.status_code == 200
    assert presence.json()['in_watchlist'] is True

    await _login(async_client, telegram_user_id=910012)
    wl = await async_client.get(f'/api/users/{me["id"]}/watchlist')
    assert wl.status_code == 200
    data = wl.json()
    assert len(data['items']) == 1
    assert data['items'][0]['film_id'] == film.id
    assert data['next_cursor'] is None


@pytest.mark.asyncio
async def test_post_watchlist_duplicate_returns_409(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=910020)
    film = await _create_film(kinopoisk_id=910021)
    first = await async_client.post('/api/me/watchlist', json={'film_id': film.id})
    assert first.status_code == 200
    second = await async_client.post('/api/me/watchlist', json={'film_id': film.id})
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_post_watchlist_blocked_when_card_exists_returns_422(
    async_client: AsyncClient,
) -> None:
    await _login(async_client, telegram_user_id=910030)
    film = await _create_film(kinopoisk_id=910031)
    card = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': list(film.genres or []),
            'rating': 8,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert card.status_code == 200
    wl_try = await async_client.post('/api/me/watchlist', json={'film_id': film.id})
    assert wl_try.status_code == 422


@pytest.mark.asyncio
async def test_delete_watchlist_not_found_returns_404(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=910040)
    film = await _create_film(kinopoisk_id=910041)
    r = await async_client.delete(f'/api/me/watchlist/films/{film.id}')
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_delete_watchlist_success(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=910050)
    film = await _create_film(kinopoisk_id=910051)
    add = await async_client.post('/api/me/watchlist', json={'film_id': film.id})
    assert add.status_code == 200
    delete = await async_client.delete(f'/api/me/watchlist/films/{film.id}')
    assert delete.status_code == 204
    presence = await async_client.get(f'/api/me/watchlist/films/{film.id}')
    assert presence.json()['in_watchlist'] is False


@pytest.mark.asyncio
async def test_create_card_removes_watchlist_entry(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=910060)
    film = await _create_film(kinopoisk_id=910061)

    wl = await async_client.post('/api/me/watchlist', json={'film_id': film.id})
    assert wl.status_code == 200

    presence_before = await async_client.get(f'/api/me/watchlist/films/{film.id}')
    assert presence_before.json()['in_watchlist'] is True

    card = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': list(film.genres or []),
            'rating': 7,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert card.status_code == 200

    presence_after = await async_client.get(f'/api/me/watchlist/films/{film.id}')
    assert presence_after.json()['in_watchlist'] is False


@pytest.mark.asyncio
async def test_list_user_watchlist_unknown_user_returns_404(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=910070)
    r = await async_client.get(f'/api/users/{uuid4()}/watchlist')
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_post_watchlist_film_not_found_returns_404(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=910080)
    r = await async_client.post('/api/me/watchlist', json={'film_id': 999999991})
    assert r.status_code == 404
