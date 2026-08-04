from __future__ import annotations

import pytest

from core.database import get_session_factory
from models.film import Film
from services.franchises.franchise_label import (
    franchise_fallback_label,
    parse_franchise_tmdb_collection_id,
    resolve_franchise_label,
)


def test_parse_franchise_tmdb_collection_id() -> None:
    assert parse_franchise_tmdb_collection_id('tmdb_collection:10') == 10
    assert parse_franchise_tmdb_collection_id('kp_franchise:10') is None


def test_franchise_fallback_label_for_tmdb_collection() -> None:
    assert franchise_fallback_label('tmdb_collection:42') == 'Коллекция #42'


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
