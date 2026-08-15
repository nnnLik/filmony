from __future__ import annotations

from providers.tmdb.tmdb_snapshot_recommendations import (
    TmdbRecommendationEntry,
    extract_tmdb_recommendation_entries,
    extract_tmdb_recommendation_titles,
)


def test_extract_tmdb_recommendation_entries_limits_and_skips_invalid() -> None:
    snapshot = {
        'recommendations': {
            'results': [
                {'id': 550, 'title': '  Se7en  '},
                {'id': 'bad', 'title': ''},
                {'id': 42, 'title': 42},
                {'title': 'The Game'},
                {'id': 111, 'title': 'Panic Room'},
                {'id': 222, 'title': 'Zodiac'},
                {'id': 333, 'title': 'Memento'},
                {'id': 444, 'title': 'Extra'},
            ],
        },
    }
    assert extract_tmdb_recommendation_entries(snapshot, limit=3) == [
        TmdbRecommendationEntry(title='Se7en', tmdb_id=550),
        TmdbRecommendationEntry(title='The Game', tmdb_id=None),
        TmdbRecommendationEntry(title='Panic Room', tmdb_id=111),
    ]


def test_extract_tmdb_recommendation_entries_empty_when_missing() -> None:
    assert extract_tmdb_recommendation_entries(None) == []
    assert extract_tmdb_recommendation_entries({'recommendations': {}}) == []


def test_extract_tmdb_recommendation_titles_wrapper() -> None:
    snapshot = {
        'recommendations': {
            'results': [
                {'id': 1, 'title': 'Alpha'},
                {'id': 2, 'title': 'Beta'},
            ],
        },
    }
    assert extract_tmdb_recommendation_titles(snapshot) == ['Alpha', 'Beta']
