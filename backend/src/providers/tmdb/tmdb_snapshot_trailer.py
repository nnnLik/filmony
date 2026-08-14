from __future__ import annotations

from typing import Any

_YOUTUBE_TRAILER_URL_TEMPLATE = 'https://www.youtube.com/watch?v={key}'


def _youtube_trailer_key(item: dict[str, Any]) -> str | None:
    key = item.get('key')
    if not isinstance(key, str) or key.strip() == '':
        return None
    return key.strip()


def extract_youtube_trailer_url(snapshot: Any | None) -> str | None:
    if not isinstance(snapshot, dict):
        return None
    videos = snapshot.get('videos')
    if not isinstance(videos, dict):
        return None
    results = videos.get('results')
    if not isinstance(results, list):
        return None

    youtube_trailers: list[dict[str, Any]] = []
    for item in results:
        if not isinstance(item, dict):
            continue
        if item.get('site') != 'YouTube' or item.get('type') != 'Trailer':
            continue
        if _youtube_trailer_key(item) is None:
            continue
        youtube_trailers.append(item)

    if not youtube_trailers:
        return None

    selected = next(
        (item for item in youtube_trailers if item.get('official') is True),
        youtube_trailers[0],
    )
    key = _youtube_trailer_key(selected)
    return _YOUTUBE_TRAILER_URL_TEMPLATE.format(key=key) if key is not None else None


__all__ = ('extract_youtube_trailer_url',)
