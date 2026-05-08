"""GET /api/cards/{id}/following-ratings — подписки с оценкой того же фильма."""

from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from core.database import get_session_factory
from models.movie_card import MovieCard
from tests.api.test_profile_routes import _login, _seed_movie_card


async def _seed_movie_card_same_film(
    *,
    user_id: UUID,
    film_id: int,
    rating: float,
) -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        card = MovieCard(
            user_id=user_id,
            film_id=film_id,
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
            await session.execute(select(MovieCard).where(MovieCard.id == alice_card_id))
        ).scalar_one()
        film_id = row.film_id

    await _login(async_client, telegram_user_id=93102)
    await _seed_movie_card_same_film(
        user_id=UUID(str(dave['id'])),
        film_id=film_id,
        rating=9.0,
    )

    await _login(async_client, telegram_user_id=93103)
    await _seed_movie_card_same_film(
        user_id=UUID(str(eve['id'])),
        film_id=film_id,
        rating=10.0,
    )

    await _login(async_client, telegram_user_id=93104)

    res = await async_client.get(f'/api/cards/{alice_card_id}/following-ratings')
    assert res.status_code == 200
    items = res.json()['items']
    assert len(items) == 2
    assert items[0]['rating'] == 10.0
    assert items[0]['user_id'] == eve['id']
    assert items[1]['rating'] == 9.0
    assert items[1]['user_id'] == dave['id']


@pytest.mark.asyncio
async def test_following_ratings_unknown_card_returns_404(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=93201)
    missing = await async_client.get('/api/cards/999999999/following-ratings')
    assert missing.status_code == 404
