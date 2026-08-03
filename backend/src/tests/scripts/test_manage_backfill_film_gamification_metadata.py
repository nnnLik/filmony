"""Integration tests for manage_backfill_film_gamification_metadata selection SQL.

The backfill script must run its PostgreSQL query without errors (no ``json = json``).
Kinopoisk HTTP is never called — tests inject FakeKinopoiskGamificationTransport.
"""

from __future__ import annotations

from contextlib import contextmanager
from unittest.mock import AsyncMock, patch

import pytest
from sqlalchemy import select

from core.database import get_session_factory
from manage_backfill_film_gamification_metadata import _needs_enrichment, _run
from models.film import Film
from providers.kinopoisk.kinopoisk_provider_transport import KinopoiskProviderTransport
from providers.kinopoisk.kinopoisk_sequels_dto import KinopoiskSequelFilmDTO
from providers.kinopoisk.kinopoisk_staff_dto import KinopoiskStaffMemberDTO
from services.gamification.enrich_film_gamification_metadata import (
    EnrichFilmGamificationMetadataService,
)
from tests.support.fake_kinopoisk_gamification_transport import (
    FakeKinopoiskGamificationTransport,
    minimal_kinopoisk_film_dto,
)


def _no_real_kinopoisk_http() -> None:
    """Fail fast if tests accidentally call live Kinopoisk transport."""
    raise AssertionError('real Kinopoisk HTTP must not be called in tests')


@contextmanager
def _backfill_with_fake_transport(fake_transport: FakeKinopoiskGamificationTransport):
    enricher = EnrichFilmGamificationMetadataService.build(transport=fake_transport)
    with (
        patch(
            'manage_backfill_film_gamification_metadata.EnrichFilmGamificationMetadataService.build',
            return_value=enricher,
        ),
        patch.object(
            KinopoiskProviderTransport,
            'get_film_by_id',
            new_callable=AsyncMock,
            side_effect=_no_real_kinopoisk_http,
        ),
        patch.object(
            KinopoiskProviderTransport,
            'get_staff_by_film_id',
            new_callable=AsyncMock,
            side_effect=_no_real_kinopoisk_http,
        ),
        patch.object(
            KinopoiskProviderTransport,
            'get_sequels_and_prequels',
            new_callable=AsyncMock,
            side_effect=_no_real_kinopoisk_http,
        ),
    ):
        yield


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


async def _get_film(film_id: int) -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        row = await session.get(Film, film_id)
        assert row is not None
        return row


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
async def test_run_dry_run_uses_fake_kinopoisk_transport(prepare_db: None) -> None:
    film = await _insert_film(kinopoisk_id=9_910_004, countries=[])

    fake_transport = FakeKinopoiskGamificationTransport(
        film_dto=minimal_kinopoisk_film_dto(kinopoisk_id=film.kinopoisk_id),
        staff=(
            KinopoiskStaffMemberDTO(
                staff_id=11,
                name_ru='Director',
                name_en=None,
                profession_key='DIRECTOR',
            ),
        ),
        sequels=(KinopoiskSequelFilmDTO(film_id=999, name_ru='Other', relation_type='SEQUEL'),),
    )

    with _backfill_with_fake_transport(fake_transport):
        await _run(
            dry_run=True,
            force=False,
            sleep_s=0,
            limit=5000,
            skip_staff=False,
            skip_sequels=False,
        )

    assert film.kinopoisk_id in fake_transport.get_film_by_id_calls
    assert film.kinopoisk_id in fake_transport.get_staff_by_film_id_calls
    assert film.kinopoisk_id in fake_transport.get_sequels_and_prequels_calls


@pytest.mark.asyncio
async def test_run_updates_film_without_real_kinopoisk_http(prepare_db: None) -> None:
    film = await _insert_film(kinopoisk_id=9_910_005, countries=[])

    fake_transport = FakeKinopoiskGamificationTransport(
        film_dto=minimal_kinopoisk_film_dto(kinopoisk_id=film.kinopoisk_id),
        staff=(
            KinopoiskStaffMemberDTO(
                staff_id=42,
                name_ru='Режиссёр',
                name_en='Director',
                profession_key='DIRECTOR',
            ),
        ),
        sequels=(),
    )

    with _backfill_with_fake_transport(fake_transport):
        await _run(
            dry_run=False,
            force=False,
            sleep_s=0,
            limit=5000,
            skip_staff=False,
            skip_sequels=False,
        )

    updated = await _get_film(film.id)
    assert updated.countries == ['США', 'Австралия']
    assert updated.primary_director_kinopoisk_id == 42
    assert updated.primary_director_name == 'Режиссёр'
    assert updated.franchise_key == f'kp_franchise:{film.kinopoisk_id}'
    assert film.kinopoisk_id in fake_transport.get_film_by_id_calls
