from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from conf import settings
from core.database import get_session_factory
from models.catalog_item import CatalogItem
from models.film import Film
from tests.auth.telegram_init_data import build_init_data


async def _login(async_client: AsyncClient, telegram_user_id: int) -> None:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    r = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_catalog_resolve_kinopoisk_creates_catalog_item(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    await _login(async_client, telegram_user_id=700)

    async def fake_get_film(self: object, kinopoisk_id: int):
        from services.kinopoisk.client import KinopoiskFilmPayload

        return KinopoiskFilmPayload(
            kinopoisk_id=kinopoisk_id,
            title='Каталог-тест',
            year=2021,
            poster_url='https://example.com/cat.jpg',
            genres=['комедия'],
            short_description='Кратко.',
            description='Полное описание.',
        )

    monkeypatch.setattr('services.kinopoisk.client.KinopoiskClient.get_film', fake_get_film)

    r = await async_client.post(
        '/api/catalog/resolve',
        json={'provider': 'kinopoisk', 'url': 'https://www.kinopoisk.ru/film/777001/'},
    )
    assert r.status_code == 200
    body = r.json()
    assert body['provider'] == 'kinopoisk'
    assert body['external_id'] == '777001'
    assert body['title'] == 'Каталог-тест'
    assert body['cover_url'] == 'https://example.com/cat.jpg'
    assert body['summary'] == 'Кратко.'
    assert body['film']['kinopoisk_id'] == 777001
    assert body['film']['title'] == 'Каталог-тест'
    catalog_item_id = body['catalog_item_id']

    session_factory = get_session_factory()
    async with session_factory() as session:
        row = (
            await session.execute(select(CatalogItem).where(CatalogItem.id == catalog_item_id))
        ).scalar_one()
        assert row.provider == 'kinopoisk'
        assert row.external_id == '777001'
        film = (await session.execute(select(Film).where(Film.id == row.film_id))).scalar_one()
        assert film.kinopoisk_id == 777001


@pytest.mark.asyncio
async def test_catalog_resolve_unsupported_provider(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=701)
    r = await async_client.post(
        '/api/catalog/resolve',
        json={'provider': 'letterboxd', 'url': 'https://letterboxd.com/film/matrix/'},
    )
    assert r.status_code == 422
    assert r.json()['detail'] == 'unsupported catalog provider'


@pytest.mark.asyncio
async def test_catalog_resolve_invalid_url(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=702)
    r = await async_client.post(
        '/api/catalog/resolve',
        json={'provider': 'kinopoisk', 'url': 'https://example.com/not-kino'},
    )
    assert r.status_code == 422
