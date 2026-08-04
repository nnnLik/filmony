"""Golden tests for weighted taste match v2 on profile stats."""

from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient

from conf import settings
from core.database import get_session_factory
from models.card_tag import CardTag
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


async def _create_film(*, kinopoisk_id: int, title: str, year: int) -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title=title,
            year=year,
            poster_url='https://example.com/poster.jpg',
            genres=['драма'],
        )
        session.add(film)
        await session.commit()
        await session.refresh(film)
        return int(film.id)


async def _seed_card(
    *,
    user_id: UUID,
    film_id: int,
    kinopoisk_id: int,
    rating: float,
    tags: list[str],
    is_favorite: bool = False,
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
            is_favorite=is_favorite,
        )
        session.add(card)
        await session.flush()
        for tag in tags:
            session.add(CardTag(card_id=card.id, tag=tag))
        await session.commit()
        return card.id


@pytest.mark.asyncio
async def test_taste_match_v2_golden_scores(async_client: AsyncClient) -> None:
    owner = await _login(async_client, telegram_user_id=5400)
    owner_id = UUID(str(owner['id']))
    peer_high = await _login(async_client, telegram_user_id=5401)
    peer_low = await _login(async_client, telegram_user_id=5402)
    peer_sparse = await _login(async_client, telegram_user_id=5403)

    film_a = await _create_film(kinopoisk_id=5400001, title='Film A', year=2024)
    film_b = await _create_film(kinopoisk_id=5400002, title='Film B', year=2023)
    film_c = await _create_film(kinopoisk_id=5400003, title='Film C', year=2022)
    film_d = await _create_film(kinopoisk_id=5400004, title='Film D', year=2021)

    for film_id, kp, rating, tags, fav in (
        (film_a, 5400001, 9.0, ['noir', 'drama'], True),
        (film_b, 5400002, 8.0, ['drama'], True),
        (film_c, 5400003, 7.0, ['arthouse'], False),
        (film_d, 5400004, 6.0, ['drama'], False),
    ):
        await _seed_card(
            user_id=owner_id,
            film_id=film_id,
            kinopoisk_id=kp,
            rating=rating,
            tags=tags,
            is_favorite=fav,
        )

    peer_high_id = UUID(str(peer_high['id']))
    for film_id, kp, rating, tags, fav in (
        (film_a, 5400001, 9.5, ['noir', 'drama'], True),
        (film_b, 5400002, 8.5, ['drama'], True),
        (film_c, 5400003, 7.5, ['arthouse'], False),
    ):
        await _seed_card(
            user_id=peer_high_id,
            film_id=film_id,
            kinopoisk_id=kp,
            rating=rating,
            tags=tags,
            is_favorite=fav,
        )

    await _seed_card(
        user_id=UUID(str(peer_low['id'])),
        film_id=film_a,
        kinopoisk_id=5400001,
        rating=3.0,
        tags=['action'],
    )
    await _seed_card(
        user_id=UUID(str(peer_low['id'])),
        film_id=film_b,
        kinopoisk_id=5400002,
        rating=4.0,
        tags=['action'],
    )
    await _seed_card(
        user_id=UUID(str(peer_low['id'])),
        film_id=film_c,
        kinopoisk_id=5400003,
        rating=5.0,
        tags=['action'],
    )

    await _seed_card(
        user_id=UUID(str(peer_sparse['id'])),
        film_id=film_a,
        kinopoisk_id=5400001,
        rating=8.0,
        tags=['drama'],
    )
    await _seed_card(
        user_id=UUID(str(peer_sparse['id'])),
        film_id=film_b,
        kinopoisk_id=5400002,
        rating=8.0,
        tags=['drama'],
    )

    for follower_tid in (5401, 5402, 5403):
        await _login(async_client, telegram_user_id=follower_tid)
        assert (await async_client.post(f'/api/users/{owner_id}/subscriptions')).status_code == 204

    await _login(async_client, telegram_user_id=5400)
    r = await async_client.get(f'/api/users/{owner_id}/stats')
    assert r.status_code == 200
    peers = r.json()['social']['taste_peers']

    assert len(peers) == 2
    assert peers[0]['id'] == peer_high['id']
    assert peers[1]['id'] == peer_low['id']
    assert peer_sparse['id'] not in {p['id'] for p in peers}

    high = peers[0]
    assert high['similarity_score'] == round(3 / (4 + 3 - 3), 3)
    assert high['score_v2'] > peers[1]['score_v2']
    assert high['breakdown']['shared_titles'] == round(3 / 4, 3)
    assert high['breakdown']['tag_overlap'] > 0.5
    assert high['breakdown']['rating_agreement'] > 0.9
    assert high['breakdown']['shared_favorites'] == 1.0

    low = peers[1]
    assert low['breakdown']['rating_agreement'] > 0
    assert low['score_v2'] < high['score_v2']
