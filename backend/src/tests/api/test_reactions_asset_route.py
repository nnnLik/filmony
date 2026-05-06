"""GET /api/reactions/asset/{key} — валидация ключа и режим без прокси RustFS."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from conf import settings


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
