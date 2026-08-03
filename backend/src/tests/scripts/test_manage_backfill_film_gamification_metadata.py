"""Integration tests for manage_backfill_film_gamification_metadata selection SQL.

The backfill script must run its PostgreSQL query without errors (no ``json = json``).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from core.database import get_session_factory
from manage_backfill_film_gamification_metadata import _needs_enrichment, _run
from models.film import Film
from services.gamification.enrich_film_gamification_metadata import FilmGamificationMetadataPreview


async def _insert_film(
    *,
    kinopoisk_id: int,
    countries: list[str] | None = None,
    primary_director_kinopoisk_id: int | None = None,
    primary_director_name: str | None = None,
    franchise_key: str | None = None,
) -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title=f'Backfill test {kinopoisk_id}',
            year=2020,
            poster_url=None,
            genres=['drama'],
            countries=countries if countries is not None else [],
            primary_director_kinopoisk_id=primary_director_kinopoisk_id,
            primary_director_name=primary_director_name,
            franchise_key=franchise_key,
        )
        session.add(film)
        await session.commit()
        await session.refresh(film)
        return film


async def _ids_needing_enrichment(*, force: bool = False, limit: int | None = None) -> list[int]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        q = select(Film.id).where(_needs_enrichment(force)).order_by(Film.id.asc())
        if limit is not None:
            q = q.limit(limit)
        result = await session.execute(q)
        return [int(row[0]) for row in result.all()]


@pytest.mark.asyncio
async def test_needs_enrichment_query_runs_on_postgres_with_empty_countries_json(
    prepare_db: None,
) -> None:
    """Regression: ``Film.countries == []`` breaks on PostgreSQL (json = json)."""
    film = await _insert_film(kinopoisk_id=9_910_001, countries=[])

    ids = await _ids_needing_enrichment(limit=5000)

    assert film.id in ids


@pytest.mark.asyncio
async def test_needs_enrichment_skips_fully_enriched_film(prepare_db: None) -> None:
    film = await _insert_film(
        kinopoisk_id=9_910_002,
        countries=['США'],
        primary_director_kinopoisk_id=66539,
        primary_director_name='Test Director',
        franchise_key='kp_franchise:301',
    )

    ids = await _ids_needing_enrichment(limit=5000)

    assert film.id not in ids


@pytest.mark.asyncio
async def test_needs_enrichment_selects_film_missing_director_only(prepare_db: None) -> None:
    film = await _insert_film(
        kinopoisk_id=9_910_003,
        countries=['Франция'],
        franchise_key='kp_franchise:99',
    )

    ids = await _ids_needing_enrichment(limit=5000)

    assert film.id in ids


@pytest.mark.asyncio
async def test_run_dry_run_completes_for_needing_film(prepare_db: None) -> None:
    film = await _insert_film(kinopoisk_id=9_910_004, countries=[])

    preview = FilmGamificationMetadataPreview(
        countries=['США'],
        primary_director_kinopoisk_id=1,
        primary_director_name='Director',
        franchise_key='kp_franchise:301',
    )
    mock_preview = AsyncMock(return_value=preview)

    with patch(
        'manage_backfill_film_gamification_metadata.EnrichFilmGamificationMetadataService'
    ) as mock_service_cls:
        mock_service_cls.build.return_value.preview = mock_preview
        await _run(
            dry_run=True,
            force=False,
            sleep_s=0,
            limit=5000,
            skip_staff=False,
            skip_sequels=False,
        )

    assert mock_preview.await_count >= 1
    called_kp_ids = [call.kwargs['kinopoisk_id'] for call in mock_preview.await_args_list]
    assert film.kinopoisk_id in called_kp_ids
