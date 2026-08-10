"""GET /api/catalog/films — browse community-rated films."""

from __future__ import annotations

import datetime as dt
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select, update

from conf import settings
from core.database import get_session_factory
from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from models.user import User
from models.user_card import UserCard
from tests.auth.telegram_init_data import build_init_data
from tests.support.user_card_category import ensure_default_category


async def _login(async_client: AsyncClient, telegram_user_id: int) -> dict:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    response = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert response.status_code == 200
    return response.json()


async def _seed_rated_film(
    *,
    telegram_user_id: int,
    kinopoisk_id: int,
    title: str,
    rating: float = 8.0,
    created_at: dt.datetime | None = None,
) -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user_id = (
            await session.execute(
                select(User.id).where(User.telegram_user_id == telegram_user_id),
            )
        ).scalar_one()
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title=title,
            year=2012,
            genres=['драма'],
            primary_director_kinopoisk_id=kinopoisk_id % 100_000,
            primary_director_name='Catalog Director',
        )
        session.add(film)
        await session.flush()
        catalog = CatalogItem(
            provider=CatalogProvider.kinopoisk,
            external_id=str(kinopoisk_id),
            film_id=film.id,
        )
        session.add(catalog)
        await session.flush()
        cat_id = await ensure_default_category(session, user_id)
        card = UserCard(
            user_id=user_id,
            film_id=film.id,
            catalog_item_id=int(catalog.id),
            provider=CatalogProvider.kinopoisk,
            category_id=cat_id,
            rating=rating,
            company='alone',
            mood_before='relax',
            mood_after='enjoyed',
        )
        session.add(card)
        await session.flush()
        if created_at is not None:
            await session.execute(
                update(UserCard).where(UserCard.id == card.id).values(created_at=created_at),
            )
        await session.commit()
        await session.refresh(film)
        return film


async def _add_rating_for_film(
    *,
    telegram_user_id: int,
    film: Film,
    rating: float,
    created_at: dt.datetime | None = None,
) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user_id = (
            await session.execute(
                select(User.id).where(User.telegram_user_id == telegram_user_id),
            )
        ).scalar_one()
        catalog_id = (
            await session.execute(
                select(CatalogItem.id).where(CatalogItem.film_id == film.id),
            )
        ).scalar_one()
        cat_id = await ensure_default_category(session, user_id)
        card = UserCard(
            user_id=user_id,
            film_id=film.id,
            catalog_item_id=int(catalog_id),
            provider=CatalogProvider.kinopoisk,
            category_id=cat_id,
            rating=rating,
            company='alone',
            mood_before='relax',
            mood_after='enjoyed',
        )
        session.add(card)
        await session.flush()
        if created_at is not None:
            await session.execute(
                update(UserCard).where(UserCard.id == card.id).values(created_at=created_at),
            )
        await session.commit()


@pytest.mark.asyncio
async def test_catalog_films_popularity_all_time(async_client: AsyncClient) -> None:
    suffix = uuid4().int % 100_000
    await _login(async_client, 94001)
    film = await _seed_rated_film(
        telegram_user_id=94001,
        kinopoisk_id=1_000_000 + suffix,
        title='Catalog Popular Film',
    )

    await _login(async_client, 94001)
    res = await async_client.get('/api/catalog/films', params={'sort': 'popularity'})
    assert res.status_code == 200
    body = res.json()
    match = [item for item in body['items'] if item['film_id'] == film.id]
    assert len(match) == 1
    assert match[0]['ratings_count'] == 1
    assert match[0]['community_avg_rating'] == 8.0
    assert match[0]['my_card_id'] is not None


@pytest.mark.asyncio
async def test_catalog_films_avg_rating_excludes_low_count(async_client: AsyncClient) -> None:
    suffix = uuid4().int % 100_000
    await _login(async_client, 94002)
    lone = await _seed_rated_film(
        telegram_user_id=94002,
        kinopoisk_id=1_010_000 + suffix,
        title='One Rating Only',
        rating=10.0,
    )
    popular = await _seed_rated_film(
        telegram_user_id=94002,
        kinopoisk_id=1_010_001 + suffix,
        title='Three Ratings High',
        rating=9.0,
    )
    for tid, rating in ((94003, 9.0), (94004, 9.0)):
        await _login(async_client, tid)
        await _add_rating_for_film(telegram_user_id=tid, film=popular, rating=rating)

    await _login(async_client, 94002)
    res = await async_client.get('/api/catalog/films', params={'sort': 'avg_rating'})
    assert res.status_code == 200
    film_ids = [item['film_id'] for item in res.json()['items']]
    assert popular.id in film_ids
    assert lone.id not in film_ids


@pytest.mark.asyncio
async def test_catalog_films_period_month_excludes_old_cards(async_client: AsyncClient) -> None:
    suffix = uuid4().int % 100_000
    await _login(async_client, 94005)
    old_created = (dt.datetime.now(dt.UTC) - dt.timedelta(days=31)).replace(tzinfo=None)
    film = await _seed_rated_film(
        telegram_user_id=94005,
        kinopoisk_id=1_020_000 + suffix,
        title='Month Window Film',
        created_at=old_created,
    )

    await _login(async_client, 94005)
    all_time = await async_client.get('/api/catalog/films', params={'period': 'all_time'})
    assert all_time.status_code == 200
    all_ids = [item['film_id'] for item in all_time.json()['items']]
    assert film.id in all_ids

    month = await async_client.get('/api/catalog/films', params={'period': 'month'})
    assert month.status_code == 200
    month_ids = [item['film_id'] for item in month.json()['items']]
    assert film.id not in month_ids


@pytest.mark.asyncio
async def test_catalog_films_q_filters_title(async_client: AsyncClient) -> None:
    suffix = uuid4().int % 100_000
    await _login(async_client, 94006)
    target = await _seed_rated_film(
        telegram_user_id=94006,
        kinopoisk_id=1_030_000 + suffix,
        title='Unique Zebra Title',
    )
    await _seed_rated_film(
        telegram_user_id=94006,
        kinopoisk_id=1_030_001 + suffix,
        title='Other Movie',
    )

    await _login(async_client, 94006)
    res = await async_client.get('/api/catalog/films', params={'q': 'zebra'})
    assert res.status_code == 200
    ids = [item['film_id'] for item in res.json()['items']]
    assert ids == [target.id]


@pytest.mark.asyncio
async def test_catalog_films_validation_errors(async_client: AsyncClient) -> None:
    await _login(async_client, 94007)
    bad_sort = await async_client.get('/api/catalog/films', params={'sort': 'invalid'})
    assert bad_sort.status_code == 422

    short_q = await async_client.get('/api/catalog/films', params={'q': 'a'})
    assert short_q.status_code == 422


@pytest.mark.asyncio
async def test_catalog_films_pagination_cursor(async_client: AsyncClient) -> None:
    suffix = uuid4().int % 100_000
    await _login(async_client, 94008)
    films: list[Film] = []
    for i in range(3):
        films.append(
            await _seed_rated_film(
                telegram_user_id=94008,
                kinopoisk_id=1_040_000 + suffix + i,
                title=f'Paginated Film {i}',
                rating=5.0 + i,
            ),
        )
    for film in films:
        for extra_tid in (94009, 94010):
            await _login(async_client, extra_tid)
            await _add_rating_for_film(telegram_user_id=extra_tid, film=film, rating=7.0)

    await _login(async_client, 94008)
    first = await async_client.get('/api/catalog/films', params={'limit': 2})
    assert first.status_code == 200
    first_body = first.json()
    assert len(first_body['items']) == 2
    assert first_body['next_cursor'] is not None

    second = await async_client.get(
        '/api/catalog/films',
        params={'limit': 2, 'cursor': first_body['next_cursor']},
    )
    assert second.status_code == 200
    second_body = second.json()
    assert len(second_body['items']) >= 1
    first_ids = {item['film_id'] for item in first_body['items']}
    second_ids = {item['film_id'] for item in second_body['items']}
    assert first_ids.isdisjoint(second_ids)
