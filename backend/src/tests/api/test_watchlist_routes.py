from __future__ import annotations

import pytest
from httpx import AsyncClient

from conf import settings
from core.database import get_session_factory
from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from models.game import Game
from models.user import User
from tests.auth.telegram_init_data import build_init_data


async def _login(async_client: AsyncClient, telegram_user_id: int) -> dict[str, object]:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    r = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert r.status_code == 200
    return r.json()


async def _create_user(*, telegram_user_id: int, slug: str) -> User:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            telegram_user_id=telegram_user_id,
            profile_slug=slug,
            username=None,
            first_name=None,
            last_name=None,
            photo_url=None,
            display_name=None,
            bio=None,
            language_code=None,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def _create_film(*, kinopoisk_id: int = 700_111, title: str = 'Test Watchlist Film') -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title=title,
            year=2024,
            poster_url='https://example.com/watchlist.jpg',
            genres=['драма'],
        )
        session.add(film)
        await session.flush()
        session.add(
            CatalogItem(
                provider=CatalogProvider.kinopoisk,
                external_id=str(kinopoisk_id),
                film_id=film.id,
            )
        )
        await session.commit()
        await session.refresh(film)
        return film


async def _create_rawg_catalog(*, slug: str = 'elden-ring') -> CatalogItem:
    session_factory = get_session_factory()
    async with session_factory() as session:
        game = Game(
            rawg_id=990_001,
            slug=slug,
            name='Elden Ring',
            released='2022-02-25',
            background_image='https://example.com/elden.jpg',
        )
        session.add(game)
        await session.flush()
        ci = CatalogItem(
            provider=CatalogProvider.rawg,
            external_id=slug,
            game_id=game.id,
        )
        session.add(ci)
        await session.commit()
        await session.refresh(ci)
        return ci


@pytest.mark.asyncio
async def test_create_watchlist_entry_with_provider_meta(
    async_client: AsyncClient,
) -> None:
    await _login(async_client, telegram_user_id=910100)
    payload = {
        'card_id': 'custom:concert-2026',
        'provider_meta': {
            'provider': 'custom',
            'data': {'title': 'Concert 2026', 'display_cover_url': 'https://example.com/c.jpg'},
        },
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
    assert body['provider'] == 'kinopoisk'
    assert body['title'] == film.title


@pytest.mark.asyncio
async def test_list_user_watchlist_empty(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=910130, slug='wl-empty')
    await _login(async_client, telegram_user_id=910130)

    response = await async_client.get(f'/api/users/{user.id}/watchlist')

    assert response.status_code == 200
    body = response.json()
    assert body['items'] == []
    assert body['next_cursor'] is None


@pytest.mark.asyncio
async def test_list_user_watchlist_with_mixed_providers(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=910131, slug='wl-mixed')
    film = await _create_film(kinopoisk_id=701_010, title='Mixed Film')
    rawg_ci = await _create_rawg_catalog(slug='mixed-game')
    await _login(async_client, telegram_user_id=910131)

    assert (await async_client.post('/api/me/watchlist', json={'film_id': film.id})).status_code == 201
    assert (
        await async_client.post('/api/me/watchlist', json={'catalog_item_id': rawg_ci.id})
    ).status_code == 201
    assert (
        await async_client.post(
            '/api/me/watchlist',
            json={
                'card_id': 'custom:book-club',
                'provider_meta': {
                    'provider': 'custom',
                    'data': {'title': 'Book Club', 'display_cover_url': None},
                },
            },
        )
    ).status_code == 201

    response = await async_client.get(f'/api/users/{user.id}/watchlist?limit=10')
    assert response.status_code == 200
    body = response.json()
    assert len(body['items']) == 3
    providers = {item['provider'] for item in body['items']}
    assert providers == {'kinopoisk', 'rawg', 'custom'}


@pytest.mark.asyncio
async def test_list_user_watchlist_pagination(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=910132, slug='wl-page')
    await _login(async_client, telegram_user_id=910132)
    for idx in range(3):
        film = await _create_film(kinopoisk_id=702_000 + idx, title=f'Page Film {idx}')
        assert (
            await async_client.post('/api/me/watchlist', json={'film_id': film.id})
        ).status_code == 201

    first = await async_client.get(f'/api/users/{user.id}/watchlist?limit=2')
    assert first.status_code == 200
    first_body = first.json()
    assert len(first_body['items']) == 2
    assert first_body['next_cursor'] is not None

    second = await async_client.get(
        f'/api/users/{user.id}/watchlist?limit=2&cursor={first_body["next_cursor"]}'
    )
    assert second.status_code == 200
    second_body = second.json()
    assert len(second_body['items']) == 1
    assert second_body['next_cursor'] is None


@pytest.mark.asyncio
async def test_create_watchlist_from_catalog_item(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=910133)
    rawg_ci = await _create_rawg_catalog(slug='catalog-create')

    response = await async_client.post('/api/me/watchlist', json={'catalog_item_id': rawg_ci.id})

    assert response.status_code == 201
    body = response.json()
    assert body['provider'] == 'rawg'
    assert body['catalog_item_id'] == rawg_ci.id
    assert body['title'] == 'Elden Ring'


@pytest.mark.asyncio
async def test_watchlist_presence_and_delete(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=910134)
    film = await _create_film(kinopoisk_id=701_020)

    created = await async_client.post('/api/me/watchlist', json={'film_id': film.id})
    assert created.status_code == 201
    entry_id = created.json()['entry_id']

    presence_before = await async_client.get(f'/api/me/watchlist/films/{film.id}')
    assert presence_before.status_code == 200
    assert presence_before.json()['in_watchlist'] is True

    card_presence = await async_client.get(
        f'/api/me/watchlist/presence?card_id=kp:{film.kinopoisk_id}'
    )
    assert card_presence.status_code == 200
    assert card_presence.json()['in_watchlist'] is True

    deleted = await async_client.delete(f'/api/me/watchlist/{entry_id}')
    assert deleted.status_code == 204

    presence_after = await async_client.get(f'/api/me/watchlist/films/{film.id}')
    assert presence_after.status_code == 200
    assert presence_after.json()['in_watchlist'] is False


@pytest.mark.asyncio
async def test_delete_watchlist_by_film_id(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=910135)
    film = await _create_film(kinopoisk_id=701_021)

    assert (await async_client.post('/api/me/watchlist', json={'film_id': film.id})).status_code == 201

    deleted = await async_client.delete(f'/api/me/watchlist/films/{film.id}')
    assert deleted.status_code == 204

    presence = await async_client.get(f'/api/me/watchlist/films/{film.id}')
    assert presence.json()['in_watchlist'] is False


@pytest.mark.asyncio
async def test_list_user_watchlist_unknown_user_returns_404(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=910136)
    response = await async_client.get(
        '/api/users/f0000000-0000-4000-8000-000000000099/watchlist'
    )
    assert response.status_code == 404


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
