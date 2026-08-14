from __future__ import annotations

import datetime as dt

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from conf import settings
from core.database import get_session_factory
from models.user import User
from models.user_card import UserCard
from models.user_subscription import UserSubscription
from services.watchlist.create_watchlist_entry import CreateWatchlistEntryService
from tests.auth.telegram_init_data import build_init_data


async def _login(async_client: AsyncClient, telegram_user_id: int) -> dict[str, object]:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    r = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert r.status_code == 200
    return r.json()


async def _create_user(
    *,
    telegram_user_id: int,
    slug: str,
    display_name: str | None = None,
) -> User:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            telegram_user_id=telegram_user_id,
            profile_slug=slug,
            username=None,
            first_name=None,
            last_name=None,
            photo_url=None,
            display_name=display_name,
            bio=None,
            language_code=None,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def _create_film(*, kinopoisk_id: int, title: str) -> int:
    from models.catalog_item import CatalogItem, CatalogProvider
    from models.film import Film

    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title=title,
            year=2024,
            poster_url=f'https://example.com/{kinopoisk_id}.jpg',
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
        return int(film.id)


async def _add_mutual_subscription(user_a: User, user_b: User) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(UserSubscription(follower_user_id=user_a.id, following_user_id=user_b.id))
        session.add(UserSubscription(follower_user_id=user_b.id, following_user_id=user_a.id))
        await session.commit()


async def _add_watchlist_entry(*, user_id, card_id: str, kp_id: int) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        service = CreateWatchlistEntryService.build(session)
        await service.execute(
            actor_user_id=user_id,
            card_id=card_id,
            provider_meta={'provider': 'kinopoisk', 'data': {'kp_id': kp_id}},
            watch_tag='watch_later',
            watch_with_user_id=None,
            created_at=dt.datetime(2026, 7, 1, 12, 0, 0, tzinfo=dt.UTC),
        )


async def _mark_film_rated(*, user_id, film_id: int, rating: float = 8.0) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        card = (
            await session.execute(
                select(UserCard).where(
                    UserCard.user_id == user_id,
                    UserCard.film_id == film_id,
                )
            )
        ).scalar_one()
        card.is_planned = False
        card.rating = rating
        await session.commit()


@pytest.mark.asyncio
async def test_evening_for_two_requires_mutual_subscription(async_client: AsyncClient) -> None:
    actor = await _create_user(telegram_user_id=940001, slug='evening-actor')
    other = await _create_user(telegram_user_id=940002, slug='evening-other')
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(UserSubscription(follower_user_id=actor.id, following_user_id=other.id))
        await session.commit()

    await _login(async_client, telegram_user_id=940001)
    response = await async_client.get(
        '/api/me/watchlist/evening-for-two',
        params={'partner_user_id': str(other.id)},
    )
    assert response.status_code == 403
    assert response.json()['detail'] == 'not_mutual'


@pytest.mark.asyncio
async def test_evening_for_two_returns_shared_unrated_film(async_client: AsyncClient) -> None:
    kp_id = 940_100
    film_id = await _create_film(kinopoisk_id=kp_id, title='Evening Pick Film')
    actor = await _create_user(telegram_user_id=940010, slug='evening-pick-actor')
    partner = await _create_user(
        telegram_user_id=940011,
        slug='evening-pick-partner',
        display_name='Evening Partner',
    )
    await _add_mutual_subscription(actor, partner)
    await _add_watchlist_entry(user_id=actor.id, card_id=f'kp:{kp_id}', kp_id=kp_id)
    await _add_watchlist_entry(user_id=partner.id, card_id=f'kp:{kp_id}', kp_id=kp_id)

    await _login(async_client, telegram_user_id=940010)
    response = await async_client.get(
        '/api/me/watchlist/evening-for-two',
        params={'partner_user_id': str(partner.id)},
    )
    assert response.status_code == 200
    body = response.json()
    assert body['film_id'] == film_id
    assert body['title'] == 'Evening Pick Film'
    assert body['poster_url'] == f'https://example.com/{kp_id}.jpg'
    assert body['entry_id'] is not None
    assert body['partner']['slug'] == 'evening-pick-partner'
    assert body['partner']['display_name'] == 'Evening Partner'


@pytest.mark.asyncio
async def test_evening_for_two_excludes_already_rated_films(async_client: AsyncClient) -> None:
    kp_id = 940_200
    film_id = await _create_film(kinopoisk_id=kp_id, title='Already Rated Film')
    actor = await _create_user(telegram_user_id=940020, slug='evening-rated-actor')
    partner = await _create_user(telegram_user_id=940021, slug='evening-rated-partner')
    await _add_mutual_subscription(actor, partner)
    await _add_watchlist_entry(user_id=actor.id, card_id=f'kp:{kp_id}', kp_id=kp_id)
    await _add_watchlist_entry(user_id=partner.id, card_id=f'kp:{kp_id}', kp_id=kp_id)
    await _mark_film_rated(user_id=actor.id, film_id=film_id)

    await _login(async_client, telegram_user_id=940020)
    response = await async_client.get(
        '/api/me/watchlist/evening-for-two',
        params={'partner_user_id': str(partner.id)},
    )
    assert response.status_code == 404
    assert response.json()['detail'] == 'no_evening_pick'
