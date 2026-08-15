from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from models.film import Film
from services.films.resolve_tmdb_recommendations import (
    ResolvedRecommendationDTO,
    ResolveTmdbRecommendationsService,
)


def _execute_result(rows: list[tuple[int, object]]) -> MagicMock:
    result = MagicMock()
    result.all.return_value = rows
    return result


@pytest.mark.asyncio
async def test_resolve_tmdb_recommendations_matches_by_tmdb_id_then_title() -> None:
    session = AsyncMock()
    session.execute = AsyncMock(
        side_effect=[
            _execute_result([(10, 550), (20, 111)]),
            _execute_result([(30, 'Dark City')]),
        ],
    )
    film = Film(
        kinopoisk_id=999,
        title='Source',
        year=1999,
        poster_url=None,
        genres=[],
        tmdb_detail_snapshot_json={
            'recommendations': {
                'results': [
                    {'id': 550, 'title': 'Fight Club'},
                    {'id': 111, 'title': 'Panic Room'},
                    {'id': 9999, 'title': 'Dark City'},
                    {'id': 8888, 'title': 'Unknown Film'},
                ],
            },
        },
    )

    resolved = await ResolveTmdbRecommendationsService.build(session).execute(film)

    assert resolved == [
        ResolvedRecommendationDTO(title='Fight Club', film_id=10, in_catalog=True),
        ResolvedRecommendationDTO(title='Panic Room', film_id=20, in_catalog=True),
        ResolvedRecommendationDTO(title='Dark City', film_id=30, in_catalog=True),
        ResolvedRecommendationDTO(title='Unknown Film', film_id=None, in_catalog=False),
    ]


@pytest.mark.asyncio
async def test_resolve_tmdb_recommendations_empty_without_snapshot() -> None:
    session = AsyncMock()
    film = Film(
        kinopoisk_id=999,
        title='Source',
        year=1999,
        poster_url=None,
        genres=[],
        tmdb_detail_snapshot_json=None,
    )

    resolved = await ResolveTmdbRecommendationsService.build(session).execute(film)

    assert resolved == []
    session.execute.assert_not_called()
