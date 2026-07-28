from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient

from conf import settings
from core.database import get_session_factory
from models.catalog_item import CatalogProvider
from models.film import Film
from models.user_card import UserCard
from tests.auth.telegram_init_data import build_init_data
from tests.support.user_card_category import ensure_default_category


async def _login(async_client: AsyncClient, telegram_user_id: int) -> dict[str, object]:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    r = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert r.status_code == 200
    return r.json()


@pytest.mark.asyncio
async def test_film_community_cards_requires_auth(async_client: AsyncClient) -> None:
    r = await async_client.get('/api/films/1/community-cards')
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_film_community_cards_404_unknown_film(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=91001)
    r = await async_client.get('/api/films/999999991/community-cards')
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_film_community_cards_returns_ratings_and_notes(async_client: AsyncClient) -> None:
    data_a = await _login(async_client, telegram_user_id=91003)
    uid_a = UUID(str(data_a['id']))
    data_b = await _login(async_client, telegram_user_id=91004)
    uid_b = UUID(str(data_b['id']))

    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=910_333,
            title='УникальныйТайтлСообщества',
            year=2019,
            poster_url=None,
            genres=['драма'],
            short_description='Кратко',
            description='Длинное описание для теста.',
        )
        session.add(film)
        await session.flush()
        fid = film.id

        cat_a = await ensure_default_category(session, uid_a)
        cat_b = await ensure_default_category(session, uid_b)
        card_a = UserCard(
            user_id=uid_a,
            film_id=fid,
            category_id=cat_a,
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
            rating=8.0,
            company='alone',
            mood_before='relax',
            mood_after='enjoyed',
            watch_note='Заметка А',
        )
        card_b = UserCard(
            user_id=uid_b,
            film_id=fid,
            category_id=cat_b,
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
            rating=6.5,
            company='friends',
            mood_before='thrill',
            mood_after='tense',
            watch_note='',
        )
        session.add(card_a)
        session.add(card_b)
        await session.flush()
        cid_a = card_a.id
        cid_b = card_b.id
        await session.commit()

    await _login(async_client, telegram_user_id=91002)
    r = await async_client.get(f'/api/films/{fid}/community-cards', params={'limit': 10})
    assert r.status_code == 200
    body = r.json()
    assert body['next_cursor'] is None
    items = body['items']
    assert len(items) == 2
    by_id = {it['id']: it for it in items}
    assert by_id[cid_a]['rating'] == 8.0
    assert by_id[cid_a]['watch_note'] == 'Заметка А'
    assert by_id[cid_a]['author']['id'] == str(uid_a)
    assert by_id[cid_b]['company'] == 'friends'


@pytest.mark.asyncio
async def test_film_community_cards_invalid_cursor(async_client: AsyncClient) -> None:
    data = await _login(async_client, telegram_user_id=91005)
    uid = UUID(str(data['id']))

    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=910_444,
            title='КурсорТестФильм',
            year=2021,
            poster_url=None,
            genres=[],
        )
        session.add(film)
        await session.flush()
        fid = film.id
        cat_id = await ensure_default_category(session, uid)
        session.add(
            UserCard(
                user_id=uid,
                film_id=fid,
                category_id=cat_id,
                provider=CatalogProvider.kinopoisk,
                external_id=str(film.kinopoisk_id),
                rating=7.0,
                company='alone',
                mood_before='relax',
                mood_after='enjoyed',
            )
        )
        await session.commit()

    r = await async_client.get(f'/api/films/{fid}/community-cards', params={'cursor': 'bad'})
    assert r.status_code == 422
