from __future__ import annotations

import httpx
import pytest

from providers.youtube.youtube_oembed_client import YoutubeOembedClient
from services.catalog.resolve_youtube_video_by_url_service import ResolveYoutubeVideoByUrlService

_VIDEO_ID = 'dQw4w9WgXcQ'
_VIDEO_URL = f'https://www.youtube.com/watch?v={_VIDEO_ID}'
_SHORTS_URL = f'https://www.youtube.com/shorts/{_VIDEO_ID}'


@pytest.mark.asyncio
async def test_resolve_youtube_video_happy_path(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        'title': 'Never Gonna Give You Up',
        'thumbnail_url': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg',
        'author_name': 'Rick Astley',
    }

    async def fake_get(
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, object] | None = None,
    ) -> httpx.Response:
        assert params == {'url': _VIDEO_URL, 'format': 'json'}
        return httpx.Response(200, json=payload)

    monkeypatch.setattr(
        'providers.youtube.youtube_oembed_client.httpx_get_idempotent',
        fake_get,
    )

    dto = await ResolveYoutubeVideoByUrlService.build().execute(url=_SHORTS_URL)
    assert dto.video_id == _VIDEO_ID
    assert dto.canonical_url == _VIDEO_URL
    assert dto.title == 'Never Gonna Give You Up'
    assert dto.cover_url == 'https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg'
    assert dto.summary == 'Rick Astley'


@pytest.mark.asyncio
async def test_resolve_youtube_video_unsupported_url() -> None:
    with pytest.raises(ResolveYoutubeVideoByUrlService.UnsupportedUrlError):
        await ResolveYoutubeVideoByUrlService.build().execute(
            url='https://www.youtube.com/watch',
        )


@pytest.mark.asyncio
async def test_resolve_youtube_video_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get(
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, object] | None = None,
    ) -> httpx.Response:
        return httpx.Response(404)

    monkeypatch.setattr(
        'providers.youtube.youtube_oembed_client.httpx_get_idempotent',
        fake_get,
    )

    with pytest.raises(ResolveYoutubeVideoByUrlService.VideoNotFoundError):
        await ResolveYoutubeVideoByUrlService.build().execute(url=_VIDEO_URL)


@pytest.mark.asyncio
async def test_resolve_youtube_video_upstream_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get(
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, object] | None = None,
    ) -> httpx.Response:
        return httpx.Response(503)

    monkeypatch.setattr(
        'providers.youtube.youtube_oembed_client.httpx_get_idempotent',
        fake_get,
    )

    with pytest.raises(ResolveYoutubeVideoByUrlService.UpstreamError):
        await ResolveYoutubeVideoByUrlService.build().execute(url=_VIDEO_URL)
