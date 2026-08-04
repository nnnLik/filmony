from __future__ import annotations

import datetime as dt
from uuid import uuid4

import pytest

from core.database import get_session_factory
from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from models.user import User
from models.user_card import UserCard
from services.tmdb.film_tmdb_metadata_stats import (
    compute_film_tmdb_metadata_stats,
    format_film_tmdb_metadata_stats,
)
from tests.support.user_card_category import ensure_default_category


@pytest.mark.asyncio
async def test_compute_stats_counts_missing_and_rated(prepare_db: None) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        enriched = Film(
            kinopoisk_id=720_001,
            title='Enriched',
            year=2020,
            poster_url=None,
            genres=['drama'],
            countries=['США'],
            primary_director_kinopoisk_id=1,
            primary_director_name='Director',
            franchise_key='kp_franchise:720001',
            tmdb_id=100,
            tmdb_synced_at=dt.datetime(2020, 1, 1),
        )
        session.add(enriched)
        missing = Film(
            kinopoisk_id=720_002,
            title='Missing',
            year=2021,
            poster_url=None,
            genres=[],
            countries=[],
        )
        session.add(missing)
        await session.flush()

        user = User(id=uuid4(), telegram_user_id=720_002, profile_slug='u-rated')
        session.add(user)
        await session.flush()
        category_id = await ensure_default_category(session, user.id)
        catalog = CatalogItem(
            provider=CatalogProvider.kinopoisk,
            external_id='720002',
            film_id=missing.id,
        )
        session.add(catalog)
        await session.flush()
        session.add(
            UserCard(
                user_id=user.id,
                film_id=missing.id,
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

        stats = await compute_film_tmdb_metadata_stats(session)

    assert stats.total_films_in_db == 2
    assert stats.total_rated_films == 1
    assert stats.without_director_name == 1
    assert stats.rated_without_director_name == 1
    assert stats.with_tmdb_id == 1
    text = format_film_tmdb_metadata_stats(stats)
    assert 'Film TMDB / gamification metadata' in text
    assert 'Оценённых фильмов (backfill scope): 1' in text
    assert 'Кэш KP-поиска без карточек:         1' in text
