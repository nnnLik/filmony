from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest

from providers.playback.pleer_video_client import PleerVideoClient, PleerVideoFilmDTO

_FIXTURES = Path(__file__).resolve().parent / 'fixtures'


def test_pleer_video_film_dto_from_dict_parses_embed() -> None:
    payload = json.loads((_FIXTURES / 'pleer_video_film.json').read_text(encoding='utf-8'))
    dto = PleerVideoFilmDTO.from_dict(payload)
    assert dto.kinopoisk_id == 258687
    assert dto.title == 'Интерстеллар'
    assert dto.iframe_url == 'https://pleer.video/258687'


@pytest.mark.asyncio
async def test_pleer_video_client_resolve_returns_descriptor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = json.loads((_FIXTURES / 'pleer_video_film.json').read_text(encoding='utf-8'))

    async def fake_get(url: str, *, headers=None, params=None) -> httpx.Response:
        assert url == 'https://pleer.video/258687.json'
        return httpx.Response(200, json=payload)

    monkeypatch.setattr(
        'providers.playback.pleer_video_client.httpx_get_idempotent',
        fake_get,
    )
    client = PleerVideoClient(_api_base_url='https://pleer.video', _cache_ttl_seconds=600)
    descriptor = await client.resolve(258687)
    assert descriptor is not None
    assert descriptor.provider == 'pleer.video'
    assert descriptor.title == 'Интерстеллар'
    assert descriptor.iframe_url == 'https://pleer.video/258687'
    assert descriptor.kinopoisk_id == 258687
    assert descriptor.expires_at > datetime.now(tz=UTC)


@pytest.mark.asyncio
async def test_pleer_video_client_resolve_not_found_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_get(url: str, *, headers=None, params=None) -> httpx.Response:
        return httpx.Response(404)

    monkeypatch.setattr(
        'providers.playback.pleer_video_client.httpx_get_idempotent',
        fake_get,
    )
    client = PleerVideoClient(_api_base_url='https://pleer.video', _cache_ttl_seconds=600)
    assert await client.resolve(999999) is None


@pytest.mark.asyncio
async def test_pleer_video_client_resolve_empty_embeds_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        'kp_id': 258687,
        'title_ru': 'Интерстеллар',
        'embeds': [],
    }

    async def fake_get(url: str, *, headers=None, params=None) -> httpx.Response:
        return httpx.Response(200, json=payload)

    monkeypatch.setattr(
        'providers.playback.pleer_video_client.httpx_get_idempotent',
        fake_get,
    )
    client = PleerVideoClient(_api_base_url='https://pleer.video', _cache_ttl_seconds=600)
    assert await client.resolve(258687) is None


@pytest.mark.asyncio
async def test_pleer_video_client_resolve_empty_iframe_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        'kp_id': 258687,
        'title_ru': 'Интерстеллар',
        'embeds': [{'iframe': '   '}],
    }

    async def fake_get(url: str, *, headers=None, params=None) -> httpx.Response:
        return httpx.Response(200, json=payload)

    monkeypatch.setattr(
        'providers.playback.pleer_video_client.httpx_get_idempotent',
        fake_get,
    )
    client = PleerVideoClient(_api_base_url='https://pleer.video', _cache_ttl_seconds=600)
    assert await client.resolve(258687) is None


@pytest.mark.asyncio
async def test_pleer_video_client_resolve_missing_iframe_field_returns_none(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    payload = {
        'kp_id': 258687,
        'title_ru': 'Интерстеллар',
        'embeds': [{}],
    }

    async def fake_get(url: str, *, headers=None, params=None) -> httpx.Response:
        return httpx.Response(200, json=payload)

    monkeypatch.setattr(
        'providers.playback.pleer_video_client.httpx_get_idempotent',
        fake_get,
    )
    client = PleerVideoClient(_api_base_url='https://pleer.video', _cache_ttl_seconds=600)
    assert await client.resolve(258687) is None


@pytest.mark.asyncio
async def test_pleer_video_client_upstream_error_on_5xx(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_get(url: str, *, headers=None, params=None) -> httpx.Response:
        return httpx.Response(503)

    monkeypatch.setattr(
        'providers.playback.pleer_video_client.httpx_get_idempotent',
        fake_get,
    )
    client = PleerVideoClient(_api_base_url='https://pleer.video', _cache_ttl_seconds=600)
    with pytest.raises(PleerVideoClient.UpstreamError):
        await client.resolve(258687)
