from __future__ import annotations

from providers.tmdb.tmdb_snapshot_recommendations import extract_tmdb_recommendation_titles


def test_extract_tmdb_recommendation_titles_limits_and_skips_invalid() -> None:
    snapshot = {
        'recommendations': {
            'results': [
                {'title': '  Se7en  '},
                {'title': ''},
                {'title': 42},
                {'title': 'The Game'},
                {'title': 'Panic Room'},
                {'title': 'Zodiac'},
                {'title': 'Memento'},
                {'title': 'Extra'},
            ],
        },
    }
    assert extract_tmdb_recommendation_titles(snapshot, limit=3) == [
        'Se7en',
        'The Game',
        'Panic Room',
    ]


def test_extract_tmdb_recommendation_titles_empty_when_missing() -> None:
    assert extract_tmdb_recommendation_titles(None) == []
    assert extract_tmdb_recommendation_titles({'recommendations': {}}) == []
