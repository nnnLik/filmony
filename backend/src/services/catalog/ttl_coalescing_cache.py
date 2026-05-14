"""Short TTL in-memory caches with in-flight coalescing (tests / narrow helpers).

Catalog hot paths use :mod:`redis_catalog_cache` instead.
"""

from __future__ import annotations

import asyncio
import time
from collections.abc import Awaitable, Callable
from typing import TypeVar

from conf import settings

T_co = TypeVar('T_co')


class TtlCoalescingCache[T_co]:
    """One key → single shared awaitable while loading; entries expire after ``ttl_seconds``."""

    def __init__(self, ttl_seconds: float) -> None:
        self._ttl = ttl_seconds
        self._data: dict[str, tuple[float, T]] = {}
        self._inflight: dict[str, asyncio.Task[T_co]] = {}
        self._lock = asyncio.Lock()

    async def get_or_fetch(self, key: str, factory: Callable[[], Awaitable[T_co]]) -> T_co:
        if settings.app.is_test:
            return await factory()

        async with self._lock:
            now = time.monotonic()
            hit = self._data.get(key)
            if hit is not None:
                expires_at, val = hit
                if now < expires_at:
                    return val
            if key not in self._inflight:
                self._inflight[key] = asyncio.create_task(
                    self._run_factory(key, factory),
                )
            task = self._inflight[key]

        return await task

    async def _run_factory(self, key: str, factory: Callable[[], Awaitable[T_co]]) -> T_co:
        try:
            val = await factory()
            async with self._lock:
                self._data[key] = (time.monotonic() + self._ttl, val)
            return val
        finally:
            async with self._lock:
                self._inflight.pop(key, None)
