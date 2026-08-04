"""Golden fixtures for weighted taste match v2."""

from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient

from core.database import get_session_factory
from models.card_tag import CardTag
from models.catalog_item import CatalogProvider
from models.user_card import UserCard
from tests.api.test_profile_routes import (
    _create_shared_film,
    _login,
    _seed_movie_card_for_film,
)
from tests.support.user_card_category import ensure_default_category


async def _seed_favorite_card(
    *,
    user_id: UUID,
    film_id: int,
    kinopoisk_id: int,
    rating: float,
    tags: list[str],
) -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        cat_id = await ensure_default_category(session, user_id)
        card = UserCard(
            user_id=user_id,
            film_id=film_id,
            category_id=cat_id,
            provider=CatalogProvider.kinopoisk,
            external_id=str(kinopoisk_id),
            rating=rating,
            company='alone',
            mood_before='relax',
            mood_after='enjoyed',
            is_planned=False,
            is_favorite=True,
        )
        session.add(card)
        await session.flush()
        for tag in tags:
            session.add(CardTag(card_id=card.id, tag=tag))
        await session.commit()
        return card.id


@pytest.mark.asyncio
async def test_taste_match_v2_golden(async_client: AsyncClient) -> None:
    owner = await _login(async_client, telegram_user_id=54100)
    owner_id = UUID(str(owner['id']))
    peer_high = await _login(async_client, telegram_user_id=54101)
    peer_low = await _login(async_client, telegram_user_id=54102)
    peer_sparse = await _login(async_client, telegram_user_id=54103)

    film_a = await _create_shared_film(kinopoisk_id=5410001, title='Golden A', year=2024)
    film_b = await _create_shared_film(kinopoisk_id=5410002, title='Golden B', year=2023)
    film_c = await _create_shared_film(kinopoisk_id=5410003, title='Golden C', year=2022)
    film_extra = await _create_shared_film(kinopoisk_id=5410100, title='Peer Extra', year=2020)

    for film_id, rating, tags in (
        (film_a, 9.0, ['noir', 'fav']),
        (film_b, 8.0, ['noir', 'classic']),
        (film_c, 7.0, ['classic']),
    ):
        await _seed_favorite_card(
            user_id=owner_id,
            film_id=film_id,
            kinopoisk_id=5410000 + film_id,
            rating=rating,
            tags=tags,
        )

    peer_high_id = UUID(str(peer_high['id']))
    for film_id, rating, tags in (
        (film_a, 9.0, ['noir', 'fav']),
        (film_b, 8.5, ['noir', 'classic']),
        (film_c, 7.5, ['classic']),
    ):
        await _seed_favorite_card(
            user_id=peer_high_id,
            film_id=film_id,
            kinopoisk_id=5411000 + film_id,
            rating=rating,
            tags=tags,
        )
    await _seed_movie_card_for_film(
        user_id=peer_high_id,
        film_id=film_extra,
        kinopoisk_id=5410100,
        rating=6.0,
        tags=['extra'],
    )

    peer_low_id = UUID(str(peer_low['id']))
    for film_id, kinopoisk_id, rating, tags in (
        (film_a, 5412001, 9.0, ['noir']),
        (film_b, 5412002, 3.0, ['other']),
        (film_c, 5412003, 4.0, ['other']),
    ):
        await _seed_movie_card_for_film(
            user_id=peer_low_id,
            film_id=film_id,
            kinopoisk_id=kinopoisk_id,
            rating=rating,
            tags=tags,
        )

    await _seed_movie_card_for_film(
        user_id=UUID(str(peer_sparse['id'])),
        film_id=film_a,
        kinopoisk_id=5413001,
        rating=8.0,
        tags=['noir'],
    )

    await _login(async_client, telegram_user_id=54101)
    assert (await async_client.post(f'/api/users/{owner_id}/subscriptions')).status_code == 204
    await _login(async_client, telegram_user_id=54102)
    assert (await async_client.post(f'/api/users/{owner_id}/subscriptions')).status_code == 204
    await _login(async_client, telegram_user_id=54103)
    assert (await async_client.post(f'/api/users/{owner_id}/subscriptions')).status_code == 204

    await _login(async_client, telegram_user_id=54100)
    r = await async_client.get(f'/api/users/{owner_id}/stats')
    assert r.status_code == 200
    peers = r.json()['social']['taste_peers']
    assert len(peers) == 2
    assert peers[0]['id'] == peer_high['id']
    assert peers[0]['score_v2'] > peers[1]['score_v2']
    assert peers[0]['breakdown']['shared_titles'] == 0.75
    assert peers[0]['breakdown']['rating_agreement'] >= 0.9
    assert peer_sparse['id'] not in {p['id'] for p in peers}
    assert 'similarity_score' in peers[0]
