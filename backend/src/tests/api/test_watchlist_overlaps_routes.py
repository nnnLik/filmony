from __future__ import annotations

import datetime as dt

import pytest
from conf import settings
from core.database import get_session_factory
from httpx import AsyncClient
from models.user import User
from models.user_subscription import UserSubscription
from services.watchlist.create_watchlist_entry import CreateWatchlistEntryService
from services.watchlist.list_watchlist_overlaps import ListWatchlistOverlapsService

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
    photo_url: str | None = None,
) -> User:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            telegram_user_id=telegram_user_id,
            profile_slug=slug,
            username=None,
            first_name=None,
            last_name=None,
            photo_url=photo_url,
            display_name=display_name,
            bio=None,
            language_code=None,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def _create_film(*, kinopoisk_id: int = 700_111, title: str = 'Overlap Film') -> None:
    from models.catalog_item import CatalogItem, CatalogProvider
    from models.film import Film

    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title=title,
            year=2024,
            poster_url='https://example.com/overlap.jpg',
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


async def _add_mutual_subscription(user_a: User, user_b: User) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(UserSubscription(follower_user_id=user_a.id, following_user_id=user_b.id))
        session.add(UserSubscription(follower_user_id=user_b.id, following_user_id=user_a.id))
        await session.commit()


async def _add_watchlist_entry(
    *,
    user_id,
    card_id: str,
    kp_id: int,
    created_at: dt.datetime | None = None,
) -> None:
    created_at = created_at or dt.datetime(2026, 7, 1, 12, 0, 0, tzinfo=dt.UTC)
    session_factory = get_session_factory()
    async with session_factory() as session:
        service = CreateWatchlistEntryService.build(session)
        await service.execute(
            actor_user_id=user_id,
            card_id=card_id,
            provider_meta={'provider': 'kinopoisk', 'data': {'kp_id': kp_id}},
            watch_tag='watch_later',
            watch_with_user_id=None,
            created_at=created_at,
        )


@pytest.mark.asyncio
async def test_watchlist_overlaps_returns_empty_without_mutual_partners(
    async_client: AsyncClient,
) -> None:
    actor = await _create_user(telegram_user_id=920001, slug='overlap-solo')
    await _add_watchlist_entry(user_id=actor.id, card_id='kp:11111', kp_id=11111)
    await _login(async_client, telegram_user_id=920001)

    response = await async_client.get('/api/me/watchlist/overlaps')
    assert response.status_code == 200
    assert response.json() == {'items': []}


@pytest.mark.asyncio
async def test_watchlist_overlaps_returns_shared_titles_with_partners(
    async_client: AsyncClient,
) -> None:
    await _create_film(kinopoisk_id=920_100, title='Shared Overlap Film')
    actor = await _create_user(
        telegram_user_id=920010,
        slug='overlap-actor',
        display_name='Actor User',
    )
    partner = await _create_user(
        telegram_user_id=920011,
        slug='overlap-partner',
        display_name='Partner User',
        photo_url='https://example.com/partner.jpg',
    )
    stranger = await _create_user(telegram_user_id=920012, slug='overlap-stranger')
    await _add_mutual_subscription(actor, partner)

    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(UserSubscription(follower_user_id=stranger.id, following_user_id=actor.id))
        await session.commit()

    await _add_watchlist_entry(user_id=actor.id, card_id='kp:920100', kp_id=920_100)
    await _add_watchlist_entry(user_id=partner.id, card_id='kp:920100', kp_id=920_100)
    await _add_watchlist_entry(user_id=stranger.id, card_id='kp:920100', kp_id=920_100)
    await _add_watchlist_entry(user_id=actor.id, card_id='kp:99999', kp_id=99999)

    await _login(async_client, telegram_user_id=920010)
    response = await async_client.get('/api/me/watchlist/overlaps')
    assert response.status_code == 200
    body = response.json()
    assert len(body['items']) == 1
    item = body['items'][0]
    assert item['card_id'] == 'kp:920100'
    assert item['entry_id'] is not None
    assert item['title'] == 'Shared Overlap Film'
    assert item['poster_url'] == 'https://example.com/overlap.jpg'
    assert item['film_id'] is not None
    assert len(item['partners']) == 1
    assert item['partners'][0]['slug'] == 'overlap-partner'
    assert item['partners'][0]['display_name'] == 'Partner User'
    assert item['partners'][0]['avatar_url'] == 'https://example.com/partner.jpg'


@pytest.mark.asyncio
async def test_watchlist_overlaps_excludes_one_way_follow(
    async_client: AsyncClient,
) -> None:
    actor = await _create_user(telegram_user_id=920020, slug='overlap-oneway-actor')
    other = await _create_user(telegram_user_id=920021, slug='overlap-oneway-other')
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(UserSubscription(follower_user_id=actor.id, following_user_id=other.id))
        await session.commit()

    await _add_watchlist_entry(user_id=actor.id, card_id='kp:22222', kp_id=22222)
    await _add_watchlist_entry(user_id=other.id, card_id='kp:22222', kp_id=22222)

    async with session_factory() as session:
        page = await ListWatchlistOverlapsService.build(session).execute(actor.id, limit=20)
    assert page.items == []


@pytest.mark.asyncio
async def test_watchlist_overlaps_respects_limit(async_client: AsyncClient) -> None:
    actor = await _create_user(telegram_user_id=920030, slug='overlap-limit-actor')
    partner = await _create_user(telegram_user_id=920031, slug='overlap-limit-partner')
    await _add_mutual_subscription(actor, partner)

    for idx in range(3):
        kp_id = 930_000 + idx
        await _add_watchlist_entry(
            user_id=actor.id,
            card_id=f'kp:{kp_id}',
            kp_id=kp_id,
            created_at=dt.datetime(2026, 7, 1, idx, 0, 0, tzinfo=dt.UTC),
        )
        await _add_watchlist_entry(
            user_id=partner.id,
            card_id=f'kp:{kp_id}',
            kp_id=kp_id,
        )

    await _login(async_client, telegram_user_id=920030)
    response = await async_client.get('/api/me/watchlist/overlaps', params={'limit': 2})
    assert response.status_code == 200
    assert len(response.json()['items']) == 2


@pytest.mark.asyncio
async def test_watchlist_overlaps_requires_auth(async_client: AsyncClient) -> None:
    response = await async_client.get('/api/me/watchlist/overlaps')
    assert response.status_code == 401
