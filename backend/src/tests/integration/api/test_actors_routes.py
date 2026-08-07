"""Actor API routes."""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from conf import settings
from core.database import get_session_factory
from models.film import Film
from models.film_actor import FilmActor
from models.person import Person
from models.user import User
from models.user_card import UserCard
from tests.auth.telegram_init_data import build_init_data
from tests.support.user_card_category import ensure_default_category


async def _login(async_client: AsyncClient, telegram_user_id: int) -> None:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    response = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert response.status_code == 200


async def _seed_actor_film(
    *,
    kinopoisk_id: int,
    actor_kp_id: int,
    actor_name: str,
    role: str | None,
    telegram_user_id: int,
    rating: float,
) -> tuple[Film, Person]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title=f'Film {kinopoisk_id}',
            year=2010,
            poster_url='https://example.com/poster.jpg',
            genres=['драма'],
        )
        session.add(film)
        await session.flush()
        person = Person(
            kinopoisk_id=actor_kp_id,
            name=actor_name,
            poster_url='https://example.com/actor.jpg',
        )
        session.add(person)
        await session.flush()
        session.add(
            FilmActor(
                film_id=film.id,
                person_id=person.id,
                billing_order=1,
                role=role,
            ),
        )
        user_id = (
            await session.execute(
                select(User.id).where(User.telegram_user_id == telegram_user_id),
            )
        ).scalar_one()
        category_id = await ensure_default_category(session, user_id)
        session.add(
            UserCard(
                user_id=user_id,
                film_id=film.id,
                category_id=category_id,
                rating=rating,
                is_planned=False,
            ),
        )
        await session.commit()
        await session.refresh(film)
        await session.refresh(person)
        return film, person


@pytest.mark.asyncio
async def test_get_actor_summary_for_user(async_client: AsyncClient) -> None:
    telegram_user_id = 910001
    await _login(async_client, telegram_user_id)
    _film, person = await _seed_actor_film(
        kinopoisk_id=910001,
        actor_kp_id=733,
        actor_name='Леонардо ДиКаприо',
        role='Jack',
        telegram_user_id=telegram_user_id,
        rating=9.0,
    )

    response = await async_client.get(f'/api/actors/{person.kinopoisk_id}')
    assert response.status_code == 200
    payload = response.json()
    assert payload['name'] == 'Леонардо ДиКаприо'
    assert payload['films_count'] == 1


@pytest.mark.asyncio
async def test_list_actor_films_includes_role(async_client: AsyncClient) -> None:
    telegram_user_id = 910002
    await _login(async_client, telegram_user_id)
    film, person = await _seed_actor_film(
        kinopoisk_id=910002,
        actor_kp_id=734,
        actor_name='Actor Two',
        role='Neo',
        telegram_user_id=telegram_user_id,
        rating=8.0,
    )

    response = await async_client.get(f'/api/actors/{person.kinopoisk_id}/films')
    assert response.status_code == 200
    items = response.json()['items']
    assert len(items) == 1
    assert items[0]['film_id'] == film.id
    assert items[0]['role'] == 'Neo'
    assert items[0]['my_card_id'] is not None


@pytest.mark.asyncio
async def test_actor_summary_404_without_rated_films(async_client: AsyncClient) -> None:
    telegram_user_id = 910003
    await _login(async_client, telegram_user_id)
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(Person(kinopoisk_id=9999, name='Lonely Actor', poster_url=None))
        await session.commit()

    response = await async_client.get('/api/actors/9999')
    assert response.status_code == 404
