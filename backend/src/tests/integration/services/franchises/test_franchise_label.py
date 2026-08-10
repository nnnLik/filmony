from __future__ import annotations

import pytest

from core.database import get_session_factory
from models.film import Film
from services.franchises.franchise_label import (
    franchise_fallback_label,
    parse_franchise_tmdb_collection_id,
    resolve_franchise_label,
    resolve_franchise_labels,
)


def test_parse_franchise_tmdb_collection_id() -> None:
    assert parse_franchise_tmdb_collection_id('tmdb_collection:10') == 10
    assert parse_franchise_tmdb_collection_id('kp_franchise:10') is None


def test_franchise_fallback_label_for_tmdb_collection() -> None:
    assert franchise_fallback_label('tmdb_collection:42') == 'Коллекция #42'


@pytest.mark.asyncio
async def test_resolve_franchise_label_from_first_franchise_film(prepare_db: None) -> None:
    session_factory = get_session_factory()
    key = 'kp_franchise:301'
    async with session_factory() as session:
        for index in range(2):
            film = Film(
                kinopoisk_id=9400300 + index,
                title=f'Matrix Part {index}',
                year=1999 + index,
                poster_url=None,
                genres=[],
                franchise_key=key,
            )
            session.add(film)
        await session.commit()

    async with session_factory() as session:
        label = await resolve_franchise_label(session, key)
        assert label == 'Matrix Part 0'


@pytest.mark.asyncio
async def test_resolve_franchise_labels_batch_matches_single_resolver(prepare_db: None) -> None:
    session_factory = get_session_factory()
    kp_key = 'kp_franchise:301'
    tmdb_key = 'tmdb_collection:10'
    async with session_factory() as session:
        for index in range(2):
            session.add(
                Film(
                    kinopoisk_id=301 if index == 0 else 9400301,
                    title='Matrix' if index == 0 else 'Matrix Reloaded',
                    year=1999 + index,
                    poster_url=None,
                    genres=[],
                    franchise_key=kp_key,
                ),
            )
        session.add(
            Film(
                kinopoisk_id=888001,
                title='Star Wars',
                year=1977,
                poster_url=None,
                genres=[],
                franchise_key=tmdb_key,
                tmdb_detail_snapshot_json={
                    'belongs_to_collection': {'id': 10, 'name': 'Star Wars Collection'},
                },
            ),
        )
        await session.commit()

    async with session_factory() as session:
        batch = await resolve_franchise_labels(session, [kp_key, tmdb_key, 'unknown:key'])
        assert batch[kp_key] == 'Matrix'
        assert batch[tmdb_key] == 'Star Wars Collection'
        assert batch['unknown:key'] == franchise_fallback_label('unknown:key')

        for key in (kp_key, tmdb_key, 'unknown:key'):
            single = await resolve_franchise_label(session, key)
            assert single == batch[key]


@pytest.mark.asyncio
async def test_resolve_franchise_label_from_tmdb_snapshot(prepare_db: None) -> None:
    session_factory = get_session_factory()
    key = 'tmdb_collection:10'
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=888001,
            title='Star Wars',
            year=1977,
            poster_url=None,
            genres=[],
            franchise_key=key,
            tmdb_detail_snapshot_json={
                'belongs_to_collection': {'id': 10, 'name': 'Star Wars Collection'},
            },
        )
        session.add(film)
        await session.commit()

    async with session_factory() as session:
        label = await resolve_franchise_label(session, key)
        assert label == 'Star Wars Collection'
