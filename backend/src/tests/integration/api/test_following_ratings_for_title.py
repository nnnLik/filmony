"""GET following-ratings on film and catalog title pages."""

from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from tests.api.test_profile_routes import _login, _seed_movie_card

from core.database import get_session_factory
from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from models.game import Game
from models.user_card import UserCard
from tests.support.user_card_category import ensure_default_category


async def _seed_movie_card_same_film(*, user_id: UUID, film_id: int, rating: float) -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = (await session.execute(select(Film).where(Film.id == film_id))).scalar_one()
        cat_id = await ensure_default_category(session, user_id)
        card = UserCard(
            user_id=user_id,
            film_id=film_id,
            category_id=cat_id,
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
            rating=rating,
            company='alone',
            mood_before='relax',
            mood_after='enjoyed',
        )
        session.add(card)
        await session.flush()
        cid = card.id
        await session.commit()
        return cid


async def _create_rawg_catalog_item(*, rawg_numeric_id: int) -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        game = Game(rawg_id=rawg_numeric_id, released='2020-04-09')
        session.add(game)
        await session.flush()
        ci = CatalogItem(
            provider=CatalogProvider.rawg,
            external_id=str(rawg_numeric_id),
            game_id=int(game.id),
            film_id=None,
        )
        session.add(ci)
        await session.flush()
        cid = int(ci.id)
        await session.commit()
        return cid


@pytest.mark.asyncio
async def test_film_following_ratings_sorted_desc(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=94101)
    alice = await _login(async_client, telegram_user_id=94102)
    dave = await _login(async_client, telegram_user_id=94103)
    eve = await _login(async_client, telegram_user_id=94104)

    await _login(async_client, telegram_user_id=94101)
    await async_client.post(f'/api/users/{dave["id"]}/subscriptions')
    await async_client.post(f'/api/users/{eve["id"]}/subscriptions')

    await _login(async_client, telegram_user_id=94102)
    card_id = await _seed_movie_card(
        user_id=UUID(str(alice['id'])),
        kinopoisk_id=941010,
        title='Film Friends',
        year=2020,
        rating=6.0,
        company='alone',
        mood_after='enjoyed',
        tags=['t'],
    )
    async with get_session_factory()() as session:
        film_id = (
            await session.execute(select(UserCard.film_id).where(UserCard.id == card_id))
        ).scalar_one()

    await _login(async_client, telegram_user_id=94103)
    await _seed_movie_card_same_film(user_id=UUID(str(dave['id'])), film_id=film_id, rating=9.0)
    await _login(async_client, telegram_user_id=94104)
    await _seed_movie_card_same_film(user_id=UUID(str(eve['id'])), film_id=film_id, rating=10.0)

    await _login(async_client, telegram_user_id=94101)
    res = await async_client.get(f'/api/films/{film_id}/following-ratings')
    assert res.status_code == 200
    items = res.json()['items']
    assert len(items) == 2
    assert items[0]['rating'] == 10.0
    assert items[1]['rating'] == 9.0


@pytest.mark.asyncio
async def test_catalog_following_ratings(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=94201)
    dave = await _login(async_client, telegram_user_id=94202)

    await _login(async_client, telegram_user_id=94201)
    await async_client.post(f'/api/users/{dave["id"]}/subscriptions')

    catalog_item_id = await _create_rawg_catalog_item(rawg_numeric_id=9420101)

    async with get_session_factory()() as session:
        cat_id = await ensure_default_category(session, UUID(str(dave['id'])))
        card = UserCard(
            user_id=UUID(str(dave['id'])),
            catalog_item_id=catalog_item_id,
            category_id=cat_id,
            provider=CatalogProvider.rawg,
            external_id='9420101',
            display_title='Catalog Game',
            rating=8.0,
            company='alone',
            mood_before='relax',
            mood_after='enjoyed',
        )
        session.add(card)
        await session.commit()

    await _login(async_client, telegram_user_id=94201)
    res = await async_client.get(f'/api/catalog/items/{catalog_item_id}/following-ratings')
    assert res.status_code == 200
    assert len(res.json()['items']) == 1
    assert res.json()['items'][0]['rating'] == 8.0


@pytest.mark.asyncio
async def test_film_following_ratings_requires_auth(async_client: AsyncClient) -> None:
    res = await async_client.get('/api/films/1/following-ratings')
    assert res.status_code == 401


@pytest.mark.asyncio
async def test_film_following_ratings_unknown_film_404(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=94301)
    res = await async_client.get('/api/films/999999999/following-ratings')
    assert res.status_code == 404
