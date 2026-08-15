from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from api.films.mappers import build_film_passport_response_fields, film_passport_response_fields
from models.film import Film
from services.films.resolve_tmdb_recommendations import ResolvedRecommendationDTO


def test_film_passport_response_fields_maps_model_and_snapshot_without_recommendations() -> None:
    film = Film(
        kinopoisk_id=301,
        title='Matrix',
        year=1999,
        poster_url=None,
        genres=[],
        film_length=136,
        slogan='Welcome to the real world',
        rating_kinopoisk=8.5,
        rating_imdb=8.7,
        rating_age_limits='age16',
        tmdb_detail_snapshot_json={
            'recommendations': {
                'results': [
                    {'title': 'Dark City'},
                    {'title': 'Equilibrium'},
                ],
            },
            'videos': {
                'results': [
                    {
                        'site': 'YouTube',
                        'type': 'Trailer',
                        'key': 'matrix-trailer',
                        'official': True,
                    },
                ],
            },
            'watch/providers': {
                'results': {
                    'RU': {
                        'flatrate': [{'provider_name': 'Okko'}],
                        'rent': [{'provider_name': 'Apple TV'}],
                    },
                },
            },
        },
    )
    assert film_passport_response_fields(film) == {
        'film_length': 136,
        'slogan': 'Welcome to the real world',
        'rating_kinopoisk': 8.5,
        'rating_imdb': 8.7,
        'rating_age_limits': 'age16',
        'trailer_youtube_url': 'https://www.youtube.com/watch?v=matrix-trailer',
        'watch_providers_ru': ['Okko', 'Apple TV'],
    }


@pytest.mark.asyncio
async def test_build_film_passport_response_fields_adds_resolved_recommendations() -> None:
    film = Film(
        kinopoisk_id=301,
        title='Matrix',
        year=1999,
        poster_url=None,
        genres=[],
        tmdb_detail_snapshot_json={'recommendations': {'results': [{'title': 'Dark City'}]}},
    )
    session = AsyncMock()
    resolved = [
        ResolvedRecommendationDTO(title='Dark City', film_id=42, in_catalog=True),
    ]

    with patch(
        'api.films.mappers.ResolveTmdbRecommendationsService.build',
        return_value=AsyncMock(execute=AsyncMock(return_value=resolved)),
    ):
        fields = await build_film_passport_response_fields(session, film)

    assert fields['tmdb_recommendations'] == [
        {'title': 'Dark City', 'film_id': 42, 'in_catalog': True},
    ]
    assert fields['trailer_youtube_url'] is None
    assert fields['watch_providers_ru'] == []
