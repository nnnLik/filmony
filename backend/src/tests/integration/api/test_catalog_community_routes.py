from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient

from conf import settings
from core.database import get_session_factory
from models.catalog_item import CatalogItem, CatalogProvider
from models.game import Game
from models.user_card import UserCard
from tests.auth.telegram_init_data import build_init_data
from tests.support.user_card_category import ensure_default_category


async def _login(async_client: AsyncClient, telegram_user_id: int) -> dict[str, object]:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    r = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert r.status_code == 200
    return r.json()


async def _seed_game_catalog_item(*, rawg_id: int, name: str = 'Test Game') -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        game = Game(
            rawg_id=rawg_id,
            name=name,
            released='2020-03-15',
            background_image='https://example.com/cover.jpg',
            description='Long game description for community page.',
        )
        session.add(game)
        await session.flush()
        item = CatalogItem(
            provider=CatalogProvider.rawg,
            external_id=str(rawg_id),
            game_id=int(game.id),
            film_id=None,
        )
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return int(item.id)


@pytest.mark.asyncio
async def test_catalog_item_detail_requires_auth(async_client: AsyncClient) -> None:
    r = await async_client.get('/api/catalog/items/1')
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_catalog_item_detail_404(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=92001)
    r = await async_client.get('/api/catalog/items/999999991')
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_catalog_item_detail_game(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=92002)
    catalog_item_id = await _seed_game_catalog_item(rawg_id=920021, name='Hollow Knight')

    r = await async_client.get(f'/api/catalog/items/{catalog_item_id}')
    assert r.status_code == 200
    body = r.json()
    assert body['kind'] == 'game'
    assert body['title'] == 'Hollow Knight'
    assert body['year'] == 2020
    assert body['poster_url'] == 'https://example.com/cover.jpg'
    assert body['my_card_id'] is None


@pytest.mark.asyncio
async def test_catalog_community_cards_game_ratings(async_client: AsyncClient) -> None:
    data_a = await _login(async_client, telegram_user_id=92003)
    uid_a = UUID(str(data_a['id']))
    data_b = await _login(async_client, telegram_user_id=92004)
    uid_b = UUID(str(data_b['id']))
    catalog_item_id = await _seed_game_catalog_item(rawg_id=920041)

    session_factory = get_session_factory()
    async with session_factory() as session:
        cat_a = await ensure_default_category(session, uid_a)
        cat_b = await ensure_default_category(session, uid_b)
        card_a = UserCard(
            user_id=uid_a,
            catalog_item_id=catalog_item_id,
            film_id=None,
            category_id=cat_a,
            provider=CatalogProvider.rawg,
            external_id='920041',
            display_title='Game A',
            rating=9.0,
            company='alone',
            mood_before='relax',
            mood_after='enjoyed',
            watch_note='Отличная игра',
        )
        card_b = UserCard(
            user_id=uid_b,
            catalog_item_id=catalog_item_id,
            film_id=None,
            category_id=cat_b,
            provider=CatalogProvider.rawg,
            external_id='920041',
            display_title='Game B',
            rating=7.0,
            company='friends',
            mood_before='thrill',
            mood_after='tense',
            watch_note='',
        )
        session.add(card_a)
        session.add(card_b)
        await session.flush()
        cid_a = card_a.id
        await session.commit()

    await _login(async_client, telegram_user_id=92005)
    r = await async_client.get(
        f'/api/catalog/items/{catalog_item_id}/community-cards',
        params={'limit': 10},
    )
    assert r.status_code == 200
    items = r.json()['items']
    assert len(items) == 2
    by_id = {it['id']: it for it in items}
    assert by_id[cid_a]['rating'] == 9.0
    assert by_id[cid_a]['watch_note'] == 'Отличная игра'


@pytest.mark.asyncio
async def test_catalog_community_cards_invalid_cursor(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=92006)
    catalog_item_id = await _seed_game_catalog_item(rawg_id=920061)
    r = await async_client.get(
        f'/api/catalog/items/{catalog_item_id}/community-cards',
        params={'cursor': 'bad-cursor'},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_catalog_item_detail_my_card_id(async_client: AsyncClient) -> None:
    data = await _login(async_client, telegram_user_id=92007)
    uid = UUID(str(data['id']))
    catalog_item_id = await _seed_game_catalog_item(rawg_id=920071)

    session_factory = get_session_factory()
    async with session_factory() as session:
        cat = await ensure_default_category(session, uid)
        card = UserCard(
            user_id=uid,
            catalog_item_id=catalog_item_id,
            film_id=None,
            category_id=cat,
            provider=CatalogProvider.rawg,
            external_id='920071',
            display_title='My Game',
            rating=8.0,
            company='alone',
            mood_before='relax',
            mood_after='enjoyed',
        )
        session.add(card)
        await session.flush()
        card_id = card.id
        await session.commit()

    r = await async_client.get(f'/api/catalog/items/{catalog_item_id}')
    assert r.status_code == 200
    assert r.json()['my_card_id'] == card_id
