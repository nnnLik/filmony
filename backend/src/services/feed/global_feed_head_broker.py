"""In-process уведомления о новых элементах глобальной ленты (MVP, один worker).

При нескольких воркерах uvicorn события не шарятся между процессами — это ограничение MVP.
"""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator

import orjson

from conf import settings

_lock = asyncio.Lock()
_version: int = 0
_subscribers: set[asyncio.Queue[int]] = set()


def get_global_feed_head_version() -> int:
    return _version


def reset_global_feed_head_broker_for_tests() -> None:
    """Сброс состояния между тестами (pytest)."""
    global _version
    _version = 0
    _subscribers.clear()


async def bump_global_feed_head_version() -> int:
    """Увеличить версию и разослать подписчикам SSE."""
    global _version
    async with _lock:
        _version += 1
        v = _version
        for q in list(_subscribers):
            try:
                q.put_nowait(v)
            except Exception:
                continue
        return v


async def iter_global_feed_head_sse() -> AsyncIterator[bytes]:
    """Поток SSE: сразу текущая версия, затем каждое bump; периодический ping."""
    q: asyncio.Queue[int] = asyncio.Queue(maxsize=32)
    async with _lock:
        _subscribers.add(q)
    try:
        init = get_global_feed_head_version()
        yield b'data: ' + orjson.dumps({'version': init}) + b'\n\n'
        ping_s = 2.0 if settings.app.is_test else 25.0
        while True:
            try:
                ver = await asyncio.wait_for(q.get(), timeout=ping_s)
            except TimeoutError:
                yield b': ping\n\n'
            else:
                yield b'data: ' + orjson.dumps({'version': ver}) + b'\n\n'
    finally:
        async with _lock:
            _subscribers.discard(q)
