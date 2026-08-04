from __future__ import annotations

import httpx
import pytest

from providers.youtube.youtube_oembed_client import YoutubeOembedClient

_VIDEO_URL = 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'
_OEMBED_URL = 'https://www.youtube.com/oembed'


@pytest.mark.asyncio
async def test_fetch_success(monkeypatch: pytest.MonkeyPatch) -> None:
    payload = {
        'title': 'Test Video',
        'thumbnail_url': 'https://i.ytimg.com/vi/abc/hqdefault.jpg',
        'author_name': 'Test Channel',
    }

    async def fake_get(
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, object] | None = None,
    ) -> httpx.Response:
        assert url == _OEMBED_URL
        assert params == {'url': _VIDEO_URL, 'format': 'json'}
        return httpx.Response(200, json=payload)

    monkeypatch.setattr(
        'providers.youtube.youtube_oembed_client.httpx_get_idempotent',
        fake_get,
    )

    dto = await YoutubeOembedClient().fetch(_VIDEO_URL)
    assert dto.title == 'Test Video'
    assert dto.thumbnail_url == 'https://i.ytimg.com/vi/abc/hqdefault.jpg'
    assert dto.author_name == 'Test Channel'


@pytest.mark.asyncio
async def test_fetch_video_not_found(monkeypatch: pytest.MonkeyPatch) -> None:
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

    with pytest.raises(YoutubeOembedClient.VideoNotFoundError):
        await YoutubeOembedClient().fetch(_VIDEO_URL)


@pytest.mark.asyncio
async def test_fetch_upstream_error_on_unexpected_status(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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

    with pytest.raises(YoutubeOembedClient.UpstreamError):
        await YoutubeOembedClient().fetch(_VIDEO_URL)


@pytest.mark.asyncio
async def test_fetch_upstream_error_on_transport_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get(
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, object] | None = None,
    ) -> httpx.Response:
        raise httpx.ConnectError('connection failed')

    monkeypatch.setattr(
        'providers.youtube.youtube_oembed_client.httpx_get_idempotent',
        fake_get,
    )

    with pytest.raises(YoutubeOembedClient.UpstreamError):
        await YoutubeOembedClient().fetch(_VIDEO_URL)


@pytest.mark.asyncio
async def test_fetch_upstream_error_on_invalid_payload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get(
        url: str,
        *,
        headers: dict[str, str] | None = None,
        params: dict[str, object] | None = None,
    ) -> httpx.Response:
        return httpx.Response(200, json={'title': 'only title'})

    monkeypatch.setattr(
        'providers.youtube.youtube_oembed_client.httpx_get_idempotent',
        fake_get,
    )

    with pytest.raises(YoutubeOembedClient.UpstreamError):
        await YoutubeOembedClient().fetch(_VIDEO_URL)
