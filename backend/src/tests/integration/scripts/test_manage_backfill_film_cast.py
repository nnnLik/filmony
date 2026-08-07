from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import select

from core.database import get_session_factory
from manage_backfill_film_cast import _films_without_cast_query, _run
from models.catalog_item import CatalogProvider
from models.film import Film
from models.film_actor import FilmActor
from models.person import Person
from models.user import User
from models.user_card import UserCard
from services.cast.ensure_film_cast import EnsureFilmCastService
from tests.support.user_card_category import ensure_default_category


@pytest.mark.asyncio
async def test_films_without_cast_query_selects_rated_only(prepare_db: None) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film_rated = Film(kinopoisk_id=901, title='Rated', year=2020, poster_url=None, genres=[])
        film_planned_only = Film(
            kinopoisk_id=902, title='Planned', year=2020, poster_url=None, genres=[]
        )
        film_with_cast = Film(
            kinopoisk_id=903, title='HasCast', year=2020, poster_url=None, genres=[]
        )
        session.add_all([film_rated, film_planned_only, film_with_cast])
        await session.flush()

        user = User(telegram_user_id=901001, profile_slug=f'cast-{uuid4().hex[:8]}')
        session.add(user)
        await session.flush()
        category_id = await ensure_default_category(session, user.id)

        session.add_all(
            [
                UserCard(
                    user_id=user.id,
                    film_id=film_rated.id,
                    category_id=category_id,
                    provider=CatalogProvider.kinopoisk,
                    external_id=str(film_rated.kinopoisk_id),
                    rating=8.0,
                    company='alone',
                    mood_before='relax',
                    mood_after='enjoyed',
                    is_planned=False,
                ),
                UserCard(
                    user_id=user.id,
                    film_id=film_planned_only.id,
                    category_id=category_id,
                    provider=CatalogProvider.kinopoisk,
                    external_id=str(film_planned_only.kinopoisk_id),
                    rating=0,
                    company='alone',
                    mood_before='relax',
                    mood_after='enjoyed',
                    is_planned=True,
                ),
                UserCard(
                    user_id=user.id,
                    film_id=film_with_cast.id,
                    category_id=category_id,
                    provider=CatalogProvider.kinopoisk,
                    external_id=str(film_with_cast.kinopoisk_id),
                    rating=7.0,
                    company='alone',
                    mood_before='relax',
                    mood_after='enjoyed',
                    is_planned=False,
                ),
            ],
        )
        person = Person(kinopoisk_id=100, name='Actor', poster_url=None)
        session.add(person)
        await session.flush()
        session.add(FilmActor(film_id=film_with_cast.id, person_id=person.id, billing_order=1))
        await session.commit()
        rated_film_id = film_rated.id

    async with session_factory() as session:
        ids = list((await session.execute(_films_without_cast_query(None))).scalars().all())
    assert ids == [rated_film_id]


@pytest.mark.asyncio
async def test_backfill_dry_run_does_not_persist_cast(prepare_db: None) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(kinopoisk_id=904, title='Backfill', year=2020, poster_url=None, genres=[])
        session.add(film)
        await session.flush()

        user = User(telegram_user_id=901002, profile_slug=f'cast-{uuid4().hex[:8]}')
        session.add(user)
        await session.flush()
        category_id = await ensure_default_category(session, user.id)
        session.add(
            UserCard(
                user_id=user.id,
                film_id=film.id,
                category_id=category_id,
                provider=CatalogProvider.kinopoisk,
                external_id=str(film.kinopoisk_id),
                rating=9.0,
                company='alone',
                mood_before='relax',
                mood_after='enjoyed',
                is_planned=False,
            ),
        )
        await session.commit()

    execute_mock = AsyncMock()
    with patch.object(EnsureFilmCastService, 'execute', execute_mock):
        await _run(dry_run=True, sleep_s=0, limit=None, batch_size=10)

    execute_mock.assert_not_awaited()
    async with session_factory() as check_session:
        count = (await check_session.execute(select(FilmActor))).scalars().all()
        assert count == []


@pytest.mark.asyncio
async def test_backfill_runs_ensure_for_candidates(prepare_db: None) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(kinopoisk_id=905, title='BackfillRun', year=2020, poster_url=None, genres=[])
        session.add(film)
        await session.flush()

        user = User(telegram_user_id=901003, profile_slug=f'cast-{uuid4().hex[:8]}')
        session.add(user)
        await session.flush()
        category_id = await ensure_default_category(session, user.id)
        session.add(
            UserCard(
                user_id=user.id,
                film_id=film.id,
                category_id=category_id,
                provider=CatalogProvider.kinopoisk,
                external_id=str(film.kinopoisk_id),
                rating=8.5,
                company='alone',
                mood_before='relax',
                mood_after='enjoyed',
                is_planned=False,
            ),
        )
        await session.commit()
        film_id = film.id

    execute_mock = AsyncMock()
    with patch.object(EnsureFilmCastService, 'build') as build_mock:
        build_mock.return_value.execute = execute_mock
        await _run(dry_run=False, sleep_s=0, limit=None, batch_size=10)

    execute_mock.assert_awaited_once_with(film_id)
