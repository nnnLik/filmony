from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import patch
from uuid import uuid4

import pytest

from core.database import get_session_factory
from manage_backfill_film_tmdb_metadata import _run as backfill_run
from manage_compare_kp_tmdb_metadata import _run as compare_run
from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from models.user import User
from models.user_card import UserCard
from services.tmdb.film_tmdb_metadata_stats import compute_film_tmdb_metadata_stats
from services.tmdb.sync_film_from_tmdb import SyncFilmFromTmdbService
from tests.support.fake_tmdb_transport import FakeTmdbTransport, fight_club_movie_detail
from tests.support.user_card_category import ensure_default_category


@contextmanager
def _backfill_with_fake(fake: FakeTmdbTransport):
    syncer = SyncFilmFromTmdbService.build(transport=fake)
    with patch(
        'manage_backfill_film_tmdb_metadata.SyncFilmFromTmdbService.build',
        return_value=syncer,
    ):
        yield


@contextmanager
def _compare_with_fake(fake: FakeTmdbTransport):
    syncer = SyncFilmFromTmdbService.build(transport=fake)
    with patch(
        'manage_compare_kp_tmdb_metadata.SyncFilmFromTmdbService.build',
        return_value=syncer,
    ):
        yield


async def _seed_rated_film(*, kinopoisk_id: int, imdb_id: str | None) -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title='Fight Club',
            year=1999,
            poster_url=None,
            genres=['drama'],
            countries=[],
            imdb_id=imdb_id,
        )
        session.add(film)
        await session.flush()
        user = User(
            id=uuid4(),
            telegram_user_id=kinopoisk_id,
            profile_slug=f'u-{uuid4().hex[:8]}',
        )
        session.add(user)
        await session.flush()
        category_id = await ensure_default_category(session, user.id)
        catalog = CatalogItem(
            provider=CatalogProvider.kinopoisk,
            external_id=str(kinopoisk_id),
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
                rating=9.0,
                company='alone',
                mood_before='relax',
                mood_after='enjoyed',
                is_planned=False,
            ),
        )
        await session.commit()
        await session.refresh(film)
        return film


@pytest.mark.asyncio
async def test_backfill_then_diagnose_shows_filled_metadata(prepare_db: None) -> None:
    fake = FakeTmdbTransport(
        find_by_imdb={'tt0137523': 550},
        movies_by_id={550: fight_club_movie_detail()},
    )
    film = await _seed_rated_film(kinopoisk_id=710_001, imdb_id='tt0137523')
    session_factory = get_session_factory()

    async with session_factory() as session:
        before = await compute_film_tmdb_metadata_stats(session)
    assert before.rated_without_director_name == 1
    assert before.rated_without_franchise_key == 1
    assert before.with_tmdb_id == 0

    with _backfill_with_fake(fake):
        await backfill_run(
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
        assert row.franchise_key == 'kp_franchise:710001'
        after = await compute_film_tmdb_metadata_stats(session)

    assert after.rated_without_director_name == 0
    assert after.rated_without_franchise_key == 0
    assert after.with_tmdb_id == 1


@pytest.mark.asyncio
async def test_compare_kp_enriched_film_with_mocked_tmdb(prepare_db: None) -> None:
    fake = FakeTmdbTransport(
        find_by_imdb={'tt0137523': 550},
        movies_by_id={550: fight_club_movie_detail()},
    )
    session_factory = get_session_factory()
    film_id: int
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=710_002,
            title='Fight Club',
            year=1999,
            poster_url=None,
            genres=['drama'],
            countries=['США'],
            primary_director_kinopoisk_id=42,
            primary_director_name='David Fincher',
            franchise_key='kp_franchise:710002',
            imdb_id='tt0137523',
        )
        session.add(film)
        await session.commit()
        await session.refresh(film)
        film_id = film.id

    with _compare_with_fake(fake):
        await compare_run(
            dry_run=False,
            sleep_s=0,
            limit=10,
            allow_kp_imdb_lookup=False,
        )

    async with session_factory() as session:
        row = await session.get(Film, film_id)
        assert row is not None
        assert row.tmdb_id == 550
        assert row.primary_director_kinopoisk_id == 42
