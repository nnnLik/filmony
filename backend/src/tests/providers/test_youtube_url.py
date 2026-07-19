from __future__ import annotations

import pytest

from providers.youtube.youtube_url import (
    canonical_youtube_url,
    is_youtube_host,
    parse_video_id,
)

_VIDEO_ID = 'dQw4w9WgXcQ'


@pytest.mark.parametrize(
    ('url', 'expected'),
    [
        (f'https://www.youtube.com/watch?v={_VIDEO_ID}', _VIDEO_ID),
        (f'https://youtube.com/watch?v={_VIDEO_ID}&t=42', _VIDEO_ID),
        (f'https://youtu.be/{_VIDEO_ID}', _VIDEO_ID),
        (f'https://youtu.be/{_VIDEO_ID}?si=abc', _VIDEO_ID),
        (f'https://m.youtube.com/watch?v={_VIDEO_ID}', _VIDEO_ID),
        (f'https://www.youtube.com/shorts/{_VIDEO_ID}', _VIDEO_ID),
        (f'https://www.youtube.com/embed/{_VIDEO_ID}', _VIDEO_ID),
    ],
)
def test_parse_video_id_supported_urls(url: str, expected: str) -> None:
    assert parse_video_id(url) == expected


@pytest.mark.parametrize(
    'url',
    [
        '',
        'not-a-url',
        'https://example.com/watch?v=dQw4w9WgXcQ',
        'https://www.youtube.com/watch',
        'https://www.youtube.com/shorts/',
        'https://www.youtube.com/embed/not-valid',
    ],
)
def test_parse_video_id_returns_none_for_invalid_urls(url: str) -> None:
    assert parse_video_id(url) is None


@pytest.mark.parametrize(
    ('url', 'expected'),
    [
        (f'https://www.youtube.com/watch?v={_VIDEO_ID}', True),
        (f'https://youtu.be/{_VIDEO_ID}', True),
        (f'https://m.youtube.com/watch?v={_VIDEO_ID}', True),
        ('https://example.com/watch?v=dQw4w9WgXcQ', False),
        ('', False),
    ],
)
def test_is_youtube_host(url: str, expected: bool) -> None:
    assert is_youtube_host(url) is expected


def test_canonical_youtube_url() -> None:
    assert canonical_youtube_url(_VIDEO_ID) == f'https://www.youtube.com/watch?v={_VIDEO_ID}'
