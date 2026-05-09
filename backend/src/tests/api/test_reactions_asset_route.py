"""GET /api/reactions/asset/{key} — валидация ключа, прокси с SigV4 и режим без RustFS."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from api.reactions import routes as reactions_routes
from conf import settings
from utils.rustfs_get_object import RustfsGetObjectResult, RustfsKeyNotFoundError


@pytest.mark.asyncio
async def test_reaction_asset_requires_three_part_key(async_client: AsyncClient) -> None:
    r = await async_client.get('/api/reactions/asset/reactions/pepe')
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_reaction_asset_unknown_category_returns_404(async_client: AsyncClient) -> None:
    r = await async_client.get('/api/reactions/asset/reactions/unknown/cat.png')
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_reaction_asset_returns_503_when_proxy_disabled(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings.reaction_media, 'rustfs_internal_base_url', '')
    r = await async_client.get('/api/reactions/asset/reactions/pepe/9137-gasp.png')
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_reaction_asset_returns_bytes_when_signed_get_succeeds(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings.reaction_media, 'rustfs_internal_base_url', 'http://rustfs:9000')
    monkeypatch.setattr(settings.reaction_media, 'rustfs_bucket', 'filmony-reactions')
    monkeypatch.setattr(settings.reaction_media, 'rustfs_access_key', 'rustfsadmin')
    monkeypatch.setattr(settings.reaction_media, 'rustfs_secret_key', 'rustfsadmin')

    def fake_get(**_kwargs: object) -> RustfsGetObjectResult:
        return RustfsGetObjectResult(body=b'\x89PNG\r\n\x1a\n', content_type='image/png')

    monkeypatch.setattr(reactions_routes, 'get_rustfs_object_bytes', fake_get)

    r = await async_client.get('/api/reactions/asset/reactions/pepe/9137-gasp.png')
    assert r.status_code == 200
    assert r.headers.get('content-type') == 'image/png'
    assert r.content.startswith(b'\x89PNG')


@pytest.mark.asyncio
async def test_reaction_asset_returns_404_when_object_missing(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings.reaction_media, 'rustfs_internal_base_url', 'http://rustfs:9000')
    monkeypatch.setattr(settings.reaction_media, 'rustfs_bucket', 'filmony-reactions')
    monkeypatch.setattr(settings.reaction_media, 'rustfs_access_key', 'rustfsadmin')
    monkeypatch.setattr(settings.reaction_media, 'rustfs_secret_key', 'rustfsadmin')

    def fake_get(**_kwargs: object) -> RustfsGetObjectResult:
        raise RustfsKeyNotFoundError('NoSuchKey')

    monkeypatch.setattr(reactions_routes, 'get_rustfs_object_bytes', fake_get)

    r = await async_client.get('/api/reactions/asset/reactions/pepe/missing.png')
    assert r.status_code == 404
