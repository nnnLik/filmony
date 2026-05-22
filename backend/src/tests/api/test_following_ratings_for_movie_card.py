"""GET /api/cards/{id}/following-ratings — подписки с оценкой того же тайтла (film_id или catalog_item_id)."""


from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from core.database import get_session_factory
from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from models.game import Game
from models.user_card import UserCard
from tests.api.test_profile_routes import _login, _seed_movie_card
from tests.support.user_card_category import ensure_default_category


async def _seed_movie_card_same_film(
    *,
    user_id: UUID,
    film_id: int,
    rating: float,
) -> int:
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


async def _create_rawg_catalog_item_for_tests(*, rawg_numeric_id: int) -> tuple[int, str]:
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
        return cid, str(rawg_numeric_id)


async def _seed_movie_card_same_catalog_game(
    *,
    user_id: UUID,
    catalog_item_id: int,
    rawg_external_id: str,
    rating: float,
    display_title: str = 'RAWG Shared Game',
) -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        cat_id = await ensure_default_category(session, user_id)
        card = UserCard(
            user_id=user_id,
            film_id=None,
            catalog_item_id=catalog_item_id,
            category_id=cat_id,
            provider=CatalogProvider.rawg,
            external_id=rawg_external_id,
            display_title=display_title,
            display_cover_url='https://example.com/cover.jpg',
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


@pytest.mark.asyncio
async def test_following_ratings_lists_subscriptions_same_film_sorted_desc(
    async_client: AsyncClient,
) -> None:
    alice = await _login(async_client, telegram_user_id=93101)
    dave = await _login(async_client, telegram_user_id=93102)
    eve = await _login(async_client, telegram_user_id=93103)

    await _login(async_client, telegram_user_id=93104)
    await async_client.post(f'/api/users/{dave["id"]}/subscriptions')
    await async_client.post(f'/api/users/{eve["id"]}/subscriptions')

    await _login(async_client, telegram_user_id=93101)
    alice_card_id = await _seed_movie_card(
        user_id=UUID(str(alice['id'])),
        kinopoisk_id=931010,
        title='Shared Film',
        year=2021,
        rating=6.0,
        company='alone',
        mood_after='enjoyed',
        tags=['t'],
    )

    session_factory = get_session_factory()
    async with session_factory() as session:
        row = (
            await session.execute(select(UserCard).where(UserCard.id == alice_card_id))
        ).scalar_one()
        film_id = row.film_id

    await _login(async_client, telegram_user_id=93102)
    dave_card_id = await _seed_movie_card_same_film(
        user_id=UUID(str(dave['id'])),
        film_id=film_id,
        rating=9.0,
    )

    await _login(async_client, telegram_user_id=93103)
    eve_card_id = await _seed_movie_card_same_film(
        user_id=UUID(str(eve['id'])),
        film_id=film_id,
        rating=10.0,
    )

    await _login(async_client, telegram_user_id=93104)

    res = await async_client.get(f'/api/cards/{alice_card_id}/following-ratings')
    assert res.status_code == 200
    body = res.json()
    assert body.get('viewer_rating') is None
    items = body['items']
    assert len(items) == 2
    assert items[0]['rating'] == 10.0
    assert items[0]['user_id'] == eve['id']
    assert items[0]['movie_card_id'] == eve_card_id
    assert items[1]['rating'] == 9.0
    assert items[1]['user_id'] == dave['id']
    assert items[1]['movie_card_id'] == dave_card_id


@pytest.mark.asyncio
async def test_following_ratings_lists_subscriptions_same_rawg_catalog_sorted_desc(
    async_client: AsyncClient,
) -> None:
    alice = await _login(async_client, telegram_user_id=93501)
    dave = await _login(async_client, telegram_user_id=93502)
    eve = await _login(async_client, telegram_user_id=93503)

    await _login(async_client, telegram_user_id=93504)
    await async_client.post(f'/api/users/{dave["id"]}/subscriptions')
    await async_client.post(f'/api/users/{eve["id"]}/subscriptions')

    catalog_item_id, ext_id = await _create_rawg_catalog_item_for_tests(rawg_numeric_id=9350101)

    await _login(async_client, telegram_user_id=93501)
    alice_card_id = await _seed_movie_card_same_catalog_game(
        user_id=UUID(str(alice['id'])),
        catalog_item_id=catalog_item_id,
        rawg_external_id=ext_id,
        rating=5.5,
    )

    await _login(async_client, telegram_user_id=93502)
    dave_card_id = await _seed_movie_card_same_catalog_game(
        user_id=UUID(str(dave['id'])),
        catalog_item_id=catalog_item_id,
        rawg_external_id=ext_id,
        rating=9.0,
    )

    await _login(async_client, telegram_user_id=93503)
    eve_card_id = await _seed_movie_card_same_catalog_game(
        user_id=UUID(str(eve['id'])),
        catalog_item_id=catalog_item_id,
        rawg_external_id=ext_id,
        rating=10.0,
    )

    await _login(async_client, telegram_user_id=93504)

    res = await async_client.get(f'/api/cards/{alice_card_id}/following-ratings')
    assert res.status_code == 200
    body = res.json()
    assert body.get('viewer_rating') is None
    items = body['items']
    assert len(items) == 2
    assert items[0]['rating'] == 10.0
    assert items[0]['user_id'] == eve['id']
    assert items[0]['movie_card_id'] == eve_card_id
    assert items[1]['rating'] == 9.0
    assert items[1]['user_id'] == dave['id']
    assert items[1]['movie_card_id'] == dave_card_id


@pytest.mark.asyncio
async def test_following_ratings_includes_viewer_row_when_same_rawg_catalog(
    async_client: AsyncClient,
) -> None:
    alice = await _login(async_client, telegram_user_id=93601)
    dave = await _login(async_client, telegram_user_id=93602)
    frank = await _login(async_client, telegram_user_id=93603)

    await _login(async_client, telegram_user_id=93603)
    sub = await async_client.post(f'/api/users/{dave["id"]}/subscriptions')
    assert sub.status_code == 204

    catalog_item_id, ext_id = await _create_rawg_catalog_item_for_tests(rawg_numeric_id=9360101)

    await _login(async_client, telegram_user_id=93601)
    alice_card_id = await _seed_movie_card_same_catalog_game(
        user_id=UUID(str(alice['id'])),
        catalog_item_id=catalog_item_id,
        rawg_external_id=ext_id,
        rating=7.0,
    )

    await _login(async_client, telegram_user_id=93602)
    dave_card_id = await _seed_movie_card_same_catalog_game(
        user_id=UUID(str(dave['id'])),
        catalog_item_id=catalog_item_id,
        rawg_external_id=ext_id,
        rating=8.5,
    )

    await _login(async_client, telegram_user_id=93603)
    frank_card_id = await _seed_movie_card_same_catalog_game(
        user_id=UUID(str(frank['id'])),
        catalog_item_id=catalog_item_id,
        rawg_external_id=ext_id,
        rating=6.5,
    )

    await _login(async_client, telegram_user_id=93603)
    res = await async_client.get(f'/api/cards/{alice_card_id}/following-ratings')
    assert res.status_code == 200
    body = res.json()
    vr = body['viewer_rating']
    assert vr is not None
    assert vr['user_id'] == frank['id']
    assert vr['rating'] == 6.5
    assert vr['movie_card_id'] == frank_card_id
    items = body['items']
    assert len(items) == 1
    assert items[0]['user_id'] == dave['id']
    assert items[0]['rating'] == 8.5
    assert items[0]['movie_card_id'] == dave_card_id


@pytest.mark.asyncio
async def test_following_ratings_unknown_card_returns_404(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=93201)
    missing = await async_client.get('/api/cards/999999999/following-ratings')
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_following_ratings_includes_viewer_row_when_viewer_has_same_film_card(
    async_client: AsyncClient,
) -> None:
    alice = await _login(async_client, telegram_user_id=93301)
    dave = await _login(async_client, telegram_user_id=93302)
    frank = await _login(async_client, telegram_user_id=93303)

    await _login(async_client, telegram_user_id=93303)
    sub = await async_client.post(f'/api/users/{dave["id"]}/subscriptions')
    assert sub.status_code == 204

    await _login(async_client, telegram_user_id=93301)
    alice_card_id = await _seed_movie_card(
        user_id=UUID(str(alice['id'])),
        kinopoisk_id=933010,
        title='Viewer Same Film',
        year=2022,
        rating=7.0,
        company='alone',
        mood_after='enjoyed',
        tags=['t'],
    )

    session_factory = get_session_factory()
    async with session_factory() as session:
        row = (
            await session.execute(select(UserCard).where(UserCard.id == alice_card_id))
        ).scalar_one()
        film_id = row.film_id

    await _login(async_client, telegram_user_id=93302)
    dave_card_id = await _seed_movie_card_same_film(
        user_id=UUID(str(dave['id'])),
        film_id=film_id,
        rating=8.5,
    )

    await _login(async_client, telegram_user_id=93303)
    frank_card_id = await _seed_movie_card_same_film(
        user_id=UUID(str(frank['id'])),
        film_id=film_id,
        rating=6.25,
    )

    await _login(async_client, telegram_user_id=93303)
    res = await async_client.get(f'/api/cards/{alice_card_id}/following-ratings')
    assert res.status_code == 200
    body = res.json()
    vr = body['viewer_rating']
    assert vr is not None
    assert vr['user_id'] == frank['id']
    assert vr['rating'] == 6.25
    assert vr['movie_card_id'] == frank_card_id
    items = body['items']
    assert len(items) == 1
    assert items[0]['user_id'] == dave['id']
    assert items[0]['rating'] == 8.5
    assert items[0]['movie_card_id'] == dave_card_id


@pytest.mark.asyncio
async def test_following_ratings_viewer_row_null_when_viewing_own_card(
    async_client: AsyncClient,
) -> None:
    u = await _login(async_client, telegram_user_id=93401)
    card_id = await _seed_movie_card(
        user_id=UUID(str(u['id'])),
        kinopoisk_id=934010,
        title='Own Card',
        year=2020,
        rating=5.0,
        company='alone',
        mood_after='enjoyed',
        tags=['t'],
    )
    res = await async_client.get(f'/api/cards/{card_id}/following-ratings')
    assert res.status_code == 200
    body = res.json()
    assert body.get('viewer_rating') is None
    assert body['items'] == []
