"""Community catalog browse: directors index, genres index/detail."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from conf import settings
from core.database import get_session_factory
from lib.genre_slug import genre_slug
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
    genres: list[str],
    director_kp: int,
    director_name: str,
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
            genres=genres,
            primary_director_kinopoisk_id=director_kp,
            primary_director_name=director_name,
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
            rating=8.0,
            company='alone',
            mood_before='relax',
            mood_after='enjoyed',
        )
        session.add(card)
        await session.commit()
        await session.refresh(film)
        return film


@pytest.mark.asyncio
async def test_directors_catalog_index(async_client: AsyncClient) -> None:
    suffix = uuid4().int % 100_000
    director_kp = 60000 + suffix
    await _login(async_client, 93001)
    await _seed_rated_film(
        telegram_user_id=93001,
        kinopoisk_id=700000 + suffix,
        title='Browse Film',
        genres=['драма'],
        director_kp=director_kp,
        director_name='Browse Director',
    )

    await _login(async_client, 93001)
    res = await async_client.get('/api/directors')
    assert res.status_code == 200
    items = res.json()['items']
    match = [item for item in items if item['kinopoisk_id'] == director_kp]
    assert len(match) == 1
    assert match[0]['films_count'] >= 1


@pytest.mark.asyncio
async def test_genres_catalog_and_films(async_client: AsyncClient) -> None:
    suffix = uuid4().int % 100_000
    genre = 'фантастика'
    slug = genre_slug(genre)
    await _login(async_client, 93101)
    film = await _seed_rated_film(
        telegram_user_id=93101,
        kinopoisk_id=800000 + suffix,
        title='Sci Fi Browse',
        genres=[genre, 'приключения'],
        director_kp=70000 + suffix,
        director_name='Genre Director',
    )

    await _login(async_client, 93101)
    index = await async_client.get('/api/genres')
    assert index.status_code == 200
    genres = index.json()['items']
    assert any(item['slug'] == slug for item in genres)

    summary = await async_client.get(f'/api/genres/{slug}')
    assert summary.status_code == 200
    assert summary.json()['genre'] == genre

    films = await async_client.get(f'/api/genres/{slug}/films')
    assert films.status_code == 200
    film_ids = [item['film_id'] for item in films.json()['items']]
    assert film.id in film_ids


@pytest.mark.asyncio
async def test_user_cards_genre_filter(async_client: AsyncClient) -> None:
    suffix = uuid4().int % 100_000
    genre = 'комедия'
    slug = genre_slug(genre)
    user = await _login(async_client, 93201)
    await _seed_rated_film(
        telegram_user_id=93201,
        kinopoisk_id=900000 + suffix,
        title='Comedy Only',
        genres=[genre],
        director_kp=80000 + suffix,
        director_name='Comedy Director',
    )
    await _seed_rated_film(
        telegram_user_id=93201,
        kinopoisk_id=900001 + suffix,
        title='Drama Other',
        genres=['драма'],
        director_kp=80001 + suffix,
        director_name='Drama Director',
    )

    await _login(async_client, 93201)
    res = await async_client.get(f'/api/users/{user["id"]}/cards', params={'genre': slug})
    assert res.status_code == 200
    titles = [item['film_title'] for item in res.json()['items']]
    assert 'Comedy Only' in titles
    assert 'Drama Other' not in titles
