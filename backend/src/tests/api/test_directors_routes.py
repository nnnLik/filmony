"""Director catalog API routes."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from conf import settings
from core.database import get_session_factory
from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from models.user import User
from models.user_card import UserCard
from tests.auth.telegram_init_data import build_init_data
from tests.support.user_card_category import ensure_default_category


async def _login(async_client: AsyncClient, telegram_user_id: int) -> None:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    response = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert response.status_code == 200


async def _create_film_with_director(
    *,
    kinopoisk_id: int,
    director_kp_id: int,
    director_name: str,
    title: str,
) -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title=title,
            year=2010,
            poster_url='https://example.com/poster.jpg',
            genres=['драма', 'криминал'],
            countries=['США'],
            primary_director_kinopoisk_id=director_kp_id,
            primary_director_name=director_name,
        )
        session.add(film)
        await session.commit()
        await session.refresh(film)
        return film


async def _rate_film(
    *,
    telegram_user_id: int,
    film: Film,
    rating: float,
) -> UserCard:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user_id = (
            await session.execute(
                select(User.id).where(User.telegram_user_id == telegram_user_id),
            )
        ).scalar_one()
        category_id = await ensure_default_category(session, user_id)
        existing_catalog = (
            await session.execute(
                select(CatalogItem.id).where(CatalogItem.film_id == film.id),
            )
        ).scalar_one_or_none()
        if existing_catalog is not None:
            catalog_item_id = int(existing_catalog)
        else:
            catalog = CatalogItem(
                provider=CatalogProvider.kinopoisk,
                external_id=str(film.kinopoisk_id),
                film_id=film.id,
            )
            session.add(catalog)
            await session.flush()
            catalog_item_id = int(catalog.id)
        card = UserCard(
            user_id=user_id,
            film_id=film.id,
            catalog_item_id=catalog_item_id,
            provider=CatalogProvider.kinopoisk,
            category_id=category_id,
            rating=rating,
            company='alone',
            mood_before='relax',
            mood_after='enjoyed',
        )
        session.add(card)
        await session.commit()
        await session.refresh(card)
        return card


@pytest.mark.asyncio
async def test_director_summary_and_films(async_client: AsyncClient) -> None:
    suffix = uuid4().int % 1_000_000
    director_kp = 66539 + suffix
    film_a = await _create_film_with_director(
        kinopoisk_id=1_000_000 + suffix,
        director_kp_id=director_kp,
        director_name='Квентин Тарантино',
        title='Film A',
    )
    film_b = await _create_film_with_director(
        kinopoisk_id=1_000_001 + suffix,
        director_kp_id=director_kp,
        director_name='Квентин Тарантино',
        title='Film B',
    )
    await _create_film_with_director(
        kinopoisk_id=1_000_002 + suffix,
        director_kp_id=director_kp,
        director_name='Квентин Тарантино',
        title='Film C unrated',
    )
    await _login(async_client, 91001)
    await _login(async_client, 91002)
    await _rate_film(telegram_user_id=91001, film=film_a, rating=9.0)
    await _rate_film(telegram_user_id=91002, film=film_a, rating=7.0)
    await _rate_film(telegram_user_id=91001, film=film_b, rating=8.0)

    await _login(async_client, 91001)
    summary = await async_client.get(f'/api/directors/{director_kp}')
    assert summary.status_code == 200
    body = summary.json()
    assert body['name'] == 'Квентин Тарантино'
    assert body['films_count'] == 2
    assert body['avg_community_rating'] == 8.0

    films = await async_client.get(f'/api/directors/{director_kp}/films')
    assert films.status_code == 200
    items = films.json()['items']
    assert len(items) == 2
    assert items[0]['film_id'] == film_a.id
    assert items[0]['ratings_count'] == 2
    assert items[0]['genres'] == ['драма', 'криминал']
    assert items[0]['community_avg_rating'] == 8.0
    assert items[0]['my_card_id'] is not None


@pytest.mark.asyncio
async def test_director_not_found(async_client: AsyncClient) -> None:
    await _login(async_client, 91003)
    response = await async_client.get('/api/directors/999999')
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_director_films_pagination(async_client: AsyncClient) -> None:
    director_kp = 77777
    films = []
    await _login(async_client, 91004)
    for idx in range(3):
        film = await _create_film_with_director(
            kinopoisk_id=2000 + idx,
            director_kp_id=director_kp,
            director_name='Paginated Director',
            title=f'Paginated {idx}',
        )
        await _rate_film(telegram_user_id=91004, film=film, rating=8.0)
        films.append(film)

    await _login(async_client, 91004)
    page1 = await async_client.get(f'/api/directors/{director_kp}/films', params={'limit': 2})
    assert page1.status_code == 200
    body1 = page1.json()
    assert len(body1['items']) == 2
    assert body1['next_cursor'] is not None

    page2 = await async_client.get(
        f'/api/directors/{director_kp}/films',
        params={'limit': 2, 'cursor': body1['next_cursor']},
    )
    assert page2.status_code == 200
    body2 = page2.json()
    assert len(body2['items']) == 1


@pytest.mark.asyncio
async def test_director_films_invalid_cursor(async_client: AsyncClient) -> None:
    director_kp = 88888
    film = await _create_film_with_director(
        kinopoisk_id=3001,
        director_kp_id=director_kp,
        director_name='Cursor Director',
        title='Cursor Film',
    )
    await _login(async_client, 91005)
    await _rate_film(telegram_user_id=91005, film=film, rating=6.0)
    await _login(async_client, 91005)
    response = await async_client.get(
        f'/api/directors/{director_kp}/films',
        params={'cursor': 'bad-cursor'},
    )
    assert response.status_code == 422
