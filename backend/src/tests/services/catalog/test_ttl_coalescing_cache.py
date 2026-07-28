from __future__ import annotations

import asyncio
from unittest.mock import patch

import pytest

from services.catalog.ttl_coalescing_cache import TtlCoalescingCache


@pytest.mark.asyncio
async def test_concurrent_misses_share_single_factory() -> None:
    calls = 0

    async def factory() -> str:
        nonlocal calls
        calls += 1
        await asyncio.sleep(0.05)
        return 'done'

    cache: TtlCoalescingCache[str] = TtlCoalescingCache(60.0)
    with patch('services.catalog.ttl_coalescing_cache.settings') as s:
        s.app.is_test = False
        out = await asyncio.gather(
            cache.get_or_fetch('k', factory),
            cache.get_or_fetch('k', factory),
            cache.get_or_fetch('k', factory),
        )
        assert out == ['done', 'done', 'done']
        assert calls == 1
