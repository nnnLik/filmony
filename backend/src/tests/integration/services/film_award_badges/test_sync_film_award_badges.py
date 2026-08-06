"""Integration coverage for Oscar badge sync idempotency."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy import func, select

from core.database import get_session_factory
from models.film import Film
from models.film_award_badge import FilmAwardBadge, FilmAwardBadgeKind
from services.film_award_badges.sync_film_award_badges import SyncFilmAwardBadgesService


async def _create_film(*, kinopoisk_id: int, title: str = 'Oscar Film') -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title=title,
            year=2019,
            poster_url='https://example.com/p.jpg',
            genres=['драма'],
        )
        session.add(film)
        await session.commit()
        await session.refresh(film)
        return film


@pytest.fixture
def curated_oscars_dir(tmp_path: Path) -> Path:
    manifest = [
        {
            'sort_order': 1,
            'name': 'Winner Film',
            'year': 2019,
            'imdb_id': 'tt1111111',
            'kinopoisk_id': 900001,
            'match_method': 'imdbId',
            'is_winner': True,
            'ceremony_year': 2020,
        },
        {
            'sort_order': 2,
            'name': 'Nominee Film',
            'year': 2019,
            'imdb_id': 'tt2222222',
            'kinopoisk_id': 900002,
            'match_method': 'imdbId',
            'is_winner': False,
            'ceremony_year': 2020,
        },
        {
            'sort_order': 3,
            'name': 'Todo Film',
            'year': 2019,
            'imdb_id': 'tt3333333',
            'kinopoisk_id': 'TODO',
            'match_method': 'todo',
            'is_winner': False,
            'ceremony_year': 2020,
        },
    ]
    path = tmp_path / 'oscars_2020_kinopoisk.json'
    path.write_text(json.dumps(manifest), encoding='utf-8')
    return tmp_path


@pytest.mark.asyncio
async def test_sync_film_award_badges_is_idempotent(
    prepare_db: None,
    curated_oscars_dir: Path,
) -> None:
    await _create_film(kinopoisk_id=900001, title='Winner Film')
    await _create_film(kinopoisk_id=900002, title='Nominee Film')

    session_factory = get_session_factory()
    async with session_factory() as session:
        service = SyncFilmAwardBadgesService.build(session, curated_dir=curated_oscars_dir)
        first = await service.execute(dry_run=False)

    assert first.rows_seen == 2
    assert first.skipped_todo == 1
    assert first.matched == 2
    assert first.upserted == 2

    async with session_factory() as session:
        count = (
            await session.execute(select(func.count()).select_from(FilmAwardBadge))
        ).scalar_one()
        assert count == 2

        winner = (
            await session.execute(
                select(FilmAwardBadge).where(
                    FilmAwardBadge.kind == FilmAwardBadgeKind.oscar_best_picture_winner.value,
                ),
            )
        ).scalar_one()
        assert winner.ceremony_year == 2020

    async with session_factory() as session:
        service = SyncFilmAwardBadgesService.build(session, curated_dir=curated_oscars_dir)
        second = await service.execute(dry_run=False)

    assert second.upserted == 2

    async with session_factory() as session:
        count = (
            await session.execute(select(func.count()).select_from(FilmAwardBadge))
        ).scalar_one()
        assert count == 2


@pytest.mark.asyncio
async def test_sync_film_award_badges_dry_run_writes_nothing(
    prepare_db: None,
    curated_oscars_dir: Path,
) -> None:
    await _create_film(kinopoisk_id=900001)

    session_factory = get_session_factory()
    async with session_factory() as session:
        result = await SyncFilmAwardBadgesService.build(
            session,
            curated_dir=curated_oscars_dir,
        ).execute(dry_run=True)

    assert result.matched == 1
    assert result.upserted == 0
    assert result.unmatched_kinopoisk_ids == (900002,)

    async with session_factory() as session:
        count = (
            await session.execute(select(func.count()).select_from(FilmAwardBadge))
        ).scalar_one()
        assert count == 0
