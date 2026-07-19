from __future__ import annotations

import re
from urllib.parse import parse_qs, unquote, urlparse

_VIDEO_ID_RE = re.compile(r'^[A-Za-z0-9_-]{11}$')


def _host_key(netloc: str) -> str:
    host = netloc.lower().split('@')[-1]
    if ':' in host:
        host = host.rsplit(':', 1)[0]
    if host.startswith('www.'):
        host = host[4:]
    return host


def is_youtube_host(url: str) -> bool:
    stripped = url.strip()
    if not stripped:
        return False
    parsed = urlparse(stripped)
    if parsed.scheme not in ('http', 'https'):
        return False
    host = _host_key(parsed.netloc)
    if host == 'youtu.be':
        return True
    return host == 'youtube.com' or host.endswith('.youtube.com')


def _valid_video_id(candidate: str | None) -> str | None:
    if candidate is None:
        return None
    video_id = unquote(candidate.strip())
    if _VIDEO_ID_RE.fullmatch(video_id):
        return video_id
    return None


def parse_video_id(url: str) -> str | None:
    stripped = url.strip()
    if not stripped:
        return None
    parsed = urlparse(stripped)
    if parsed.scheme not in ('http', 'https'):
        return None
    if not is_youtube_host(stripped):
        return None

    host = _host_key(parsed.netloc)
    if host == 'youtu.be':
        segments = [segment for segment in parsed.path.split('/') if segment]
        if not segments:
            return None
        return _valid_video_id(segments[0])

    segments = [segment for segment in parsed.path.split('/') if segment]
    if not segments:
        return None

    head = segments[0].lower()
    if head == 'watch':
        if len(segments) >= 2:
            video_id = _valid_video_id(segments[1])
            if video_id is not None:
                return video_id
        query = parse_qs(parsed.query)
        v_values = query.get('v')
        if v_values:
            return _valid_video_id(v_values[0])
        return None

    if head in ('shorts', 'embed'):
        if len(segments) >= 2:
            return _valid_video_id(segments[1])
        return None

    return None


def canonical_youtube_url(video_id: str) -> str:
    return f'https://www.youtube.com/watch?v={video_id}'
