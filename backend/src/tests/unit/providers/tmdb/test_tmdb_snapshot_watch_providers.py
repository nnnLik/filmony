from __future__ import annotations

from providers.tmdb.tmdb_snapshot_watch_providers import extract_ru_watch_provider_names


def test_extract_ru_watch_provider_names_collects_unique_from_all_buckets() -> None:
    snapshot = {
        'watch/providers': {
            'results': {
                'RU': {
                    'flatrate': [
                        {'provider_name': '  Okko  '},
                        {'provider_name': 'Okko'},
                        {'provider_name': 'ivi'},
                    ],
                    'rent': [
                        {'provider_name': 'Apple TV'},
                        {'provider_name': 'ivi'},
                    ],
                    'buy': [
                        {'provider_name': 'Google Play Movies'},
                        {'provider_name': 42},
                    ],
                },
            },
        },
    }
    assert extract_ru_watch_provider_names(snapshot) == [
        'Okko',
        'ivi',
        'Apple TV',
        'Google Play Movies',
    ]


def test_extract_ru_watch_provider_names_empty_when_missing() -> None:
    assert extract_ru_watch_provider_names(None) == []
    assert extract_ru_watch_provider_names({'watch/providers': {}}) == []
    assert extract_ru_watch_provider_names({'watch/providers': {'results': {}}}) == []
    assert extract_ru_watch_provider_names({'watch/providers': {'results': {'US': {}}}}) == []
