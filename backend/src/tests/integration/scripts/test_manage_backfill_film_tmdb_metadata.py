"""Tests for manage_backfill_film_tmdb_metadata selection and sync wiring."""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from sqlalchemy import select

from core.database import get_session_factory
from manage_backfill_film_tmdb_metadata import _needs_tmdb_enrichment, _run
from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from models.user import User
from models.user_card import UserCard
from providers.tmdb.tmdb_provider_transport import TmdbProviderTransport
from services.tmdb.sync_film_from_tmdb import SyncFilmFromTmdbService
from tests.support.fake_tmdb_transport import FakeTmdbTransport, fight_club_movie_detail
from tests.support.user_card_category import ensure_default_category


def _no_real_tmdb_http() -> None:
    raise AssertionError('real TMDB HTTP must not be called in tests')


@contextmanager
def _backfill_with_fake_transport(fake_transport: FakeTmdbTransport):
    syncer = SyncFilmFromTmdbService.build(transport=fake_transport)
    with (
        patch(
            'manage_backfill_film_tmdb_metadata.SyncFilmFromTmdbService.build',
            return_value=syncer,
        ),
        patch.object(
            TmdbProviderTransport,
            'get_movie_by_id',
            new_callable=AsyncMock,
            side_effect=_no_real_tmdb_http,
        ),
    ):
        yield


async def _insert_film(**kwargs: object) -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=int(kwargs.get('kinopoisk_id', 700001)),
            title=str(kwargs.get('title', 'Test film')),
            year=int(kwargs['year']) if 'year' in kwargs else 2020,
            poster_url=None,
            genres=['drama'],
            countries=list(kwargs.get('countries', [])),
            primary_director_name=kwargs.get('primary_director_name'),
            franchise_key=kwargs.get('franchise_key'),
            imdb_id=kwargs.get('imdb_id'),
        )
        session.add(film)
        await session.commit()
        await session.refresh(film)
        return film


@pytest.mark.asyncio
async def test_needs_tmdb_enrichment_selects_missing_metadata(prepare_db: None) -> None:
    session_factory = get_session_factory()
    film = await _insert_film(kinopoisk_id=700010, countries=[], imdb_id='tt0137523')
    async with session_factory() as session:
        q = select(Film.id).where(Film.id == film.id).where(_needs_tmdb_enrichment(force=False))
        found = (await session.execute(q)).scalar_one_or_none()
        assert found == film.id


@pytest.mark.asyncio
async def test_backfill_updates_rated_film_with_fake_transport(prepare_db: None) -> None:
    fake = FakeTmdbTransport(
        find_by_imdb={'tt0137523': 550},
        movies_by_id={550: fight_club_movie_detail()},
    )
    film = await _insert_film(
        kinopoisk_id=700020,
        title='Fight Club',
        year=1999,
        imdb_id='tt0137523',
    )
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            id=uuid4(),
            telegram_user_id=700_020,
            profile_slug=f'u-{uuid4().hex[:8]}',
        )
        session.add(user)
        await session.flush()
        category_id = await ensure_default_category(session, user.id)
        catalog = CatalogItem(
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
            film_id=film.id,
        )
        session.add(catalog)
        await session.flush()
        session.add(
            UserCard(
                user_id=user.id,
                film_id=film.id,
                catalog_item_id=catalog.id,
                provider=CatalogProvider.kinopoisk,
                category_id=category_id,
                rating=8.0,
                company='alone',
                mood_before='relax',
                mood_after='enjoyed',
                is_planned=False,
            ),
        )
        await session.commit()

    with _backfill_with_fake_transport(fake):
        await _run(
            dry_run=False,
            force=False,
            force_gamification=False,
            sleep_s=0,
            limit=10,
            allow_kp_imdb_lookup=False,
        )

    async with session_factory() as session:
        row = await session.get(Film, film.id)
        assert row is not None
        assert row.tmdb_id == 550
        assert row.primary_director_name == 'David Fincher'


@pytest.mark.asyncio
async def test_backfill_skips_unrated_search_cache_film(prepare_db: None) -> None:
    fake = FakeTmdbTransport(
        find_by_imdb={'tt0137523': 550},
        movies_by_id={550: fight_club_movie_detail()},
    )
    orphan = await _insert_film(
        kinopoisk_id=700_030,
        title='Search cache orphan',
        imdb_id='tt0137523',
    )
    with _backfill_with_fake_transport(fake):
        await _run(
            dry_run=False,
            force=False,
            force_gamification=False,
            sleep_s=0,
            limit=10,
            allow_kp_imdb_lookup=False,
        )

    session_factory = get_session_factory()
    async with session_factory() as session:
        row = await session.get(Film, orphan.id)
        assert row is not None
        assert row.tmdb_id is None
        assert row.primary_director_name is None
