from __future__ import annotations

from providers.tmdb.tmdb_snapshot_trailer import extract_youtube_trailer_url


def test_extract_youtube_trailer_url_prefers_official_trailer() -> None:
    snapshot = {
        'videos': {
            'results': [
                {
                    'site': 'YouTube',
                    'type': 'Trailer',
                    'key': 'first-key',
                    'official': False,
                },
                {
                    'site': 'YouTube',
                    'type': 'Trailer',
                    'key': 'official-key',
                    'official': True,
                },
            ],
        },
    }
    assert extract_youtube_trailer_url(snapshot) == 'https://www.youtube.com/watch?v=official-key'


def test_extract_youtube_trailer_url_falls_back_to_first_youtube_trailer() -> None:
    snapshot = {
        'videos': {
            'results': [
                {'site': 'Vimeo', 'type': 'Trailer', 'key': 'skip'},
                {'site': 'YouTube', 'type': 'Teaser', 'key': 'skip-too'},
                {'site': 'YouTube', 'type': 'Trailer', 'key': 'first-key'},
                {'site': 'YouTube', 'type': 'Trailer', 'key': 'second-key'},
            ],
        },
    }
    assert extract_youtube_trailer_url(snapshot) == 'https://www.youtube.com/watch?v=first-key'


def test_extract_youtube_trailer_url_empty_when_missing() -> None:
    assert extract_youtube_trailer_url(None) is None
    assert extract_youtube_trailer_url({'videos': {}}) is None
    assert extract_youtube_trailer_url({'videos': {'results': []}}) is None
