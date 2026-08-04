"""Franchise catalog API routes."""

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


async def _create_franchise_film(
    *,
    kinopoisk_id: int,
    franchise_key: str,
    title: str,
) -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title=title,
            year=2015,
            poster_url='https://example.com/poster.jpg',
            genres=['фантастика'],
            countries=['США'],
            franchise_key=franchise_key,
        )
        session.add(film)
        await session.commit()
        await session.refresh(film)
        return film


async def _rate_film(*, telegram_user_id: int, film: Film, rating: float) -> None:
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


@pytest.mark.asyncio
async def test_franchise_summary_and_films(async_client: AsyncClient) -> None:
    suffix = uuid4().int % 1_000_000
    franchise = f'kp_franchise:{301 + suffix}'
    film_a = await _create_franchise_film(
        kinopoisk_id=301 + suffix,
        franchise_key=franchise,
        title='Franchise Root',
    )
    film_b = await _create_franchise_film(
        kinopoisk_id=500_001 + suffix,
        franchise_key=franchise,
        title='Franchise Sequel',
    )
    await _create_franchise_film(
        kinopoisk_id=500_002 + suffix,
        franchise_key=franchise,
        title='Franchise Unrated',
    )

    await _login(async_client, 92001)
    await _login(async_client, 92002)
    await _rate_film(telegram_user_id=92001, film=film_a, rating=9.0)
    await _rate_film(telegram_user_id=92002, film=film_a, rating=7.0)
    await _rate_film(telegram_user_id=92001, film=film_b, rating=8.0)

    await _login(async_client, 92001)
    summary = await async_client.get(f'/api/franchises/{franchise}')
    assert summary.status_code == 200
    body = summary.json()
    assert body['label'] == 'Franchise Root'
    assert body['films_count'] == 2
    assert body['avg_community_rating'] == 8.0

    films = await async_client.get(f'/api/franchises/{franchise}/films')
    assert films.status_code == 200
    items = films.json()['items']
    assert len(items) == 2
    assert items[0]['film_id'] == film_a.id


@pytest.mark.asyncio
async def test_franchise_not_found(async_client: AsyncClient) -> None:
    await _login(async_client, 92003)
    res = await async_client.get('/api/franchises/kp_franchise%3A999999999')
    assert res.status_code == 404
