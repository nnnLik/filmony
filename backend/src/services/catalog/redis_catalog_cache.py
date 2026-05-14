"""Redis-backed JSON cache for catalog search/resolve with in-flight coalescing."""

from __future__ import annotations

import asyncio
import hashlib
import logging
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar

from redis.asyncio import Redis

from conf.settings import settings

logger = logging.getLogger(__name__)

T = TypeVar('T')

_PREFIX = 'filmony:catalog:v1'

_redis_client: Redis | None = None
_client_lock = asyncio.Lock()

_inflight: dict[str, asyncio.Task[Any]] = {}
_inflight_lock = asyncio.Lock()

_catalog_cache_hits = 0
_catalog_cache_misses = 0
_catalog_cache_errors = 0


def catalog_cache_counters() -> dict[str, int]:
    """Best-effort counters for observability (not transactional)."""

    return {
        'hits': _catalog_cache_hits,
        'misses': _catalog_cache_misses,
        'errors': _catalog_cache_errors,
    }


def reset_catalog_cache_counters_for_tests() -> None:
    global _catalog_cache_hits, _catalog_cache_misses, _catalog_cache_errors
    _catalog_cache_hits = 0
    _catalog_cache_misses = 0
    _catalog_cache_errors = 0


def catalog_cache_redis_url() -> str | None:
    raw = (settings.catalog_cache.redis_url or '').strip()
    if raw:
        return raw
    broker = settings.celery.broker_url.strip()
    if broker.startswith(('redis://', 'rediss://')):
        return broker
    return None


async def _redis() -> Redis | None:
    global _redis_client
    url = catalog_cache_redis_url()
    if url is None:
        return None
    if _redis_client is not None:
        return _redis_client
    async with _client_lock:
        if _redis_client is None:
            _redis_client = Redis.from_url(url, decode_responses=False)
    return _redis_client


def bounded_cache_key(segment: str, logical_key: str) -> str:
    digest = hashlib.sha256(logical_key.encode('utf-8')).hexdigest()[:32]
    return f'{_PREFIX}:{segment}:{digest}'


async def _run_factory_store(
    *,
    client: Redis,
    redis_key: str,
    ttl_seconds: int,
    factory: Callable[[], Awaitable[T]],
    dumps: Callable[[T], bytes],
) -> T:
    global _catalog_cache_errors
    try:
        val = await factory()
        try:
            await client.set(redis_key, dumps(val), ex=ttl_seconds)
        except Exception:
            logger.warning('catalog_cache set failed key=%s', redis_key, exc_info=True)
            _catalog_cache_errors += 1
        return val
    finally:
        async with _inflight_lock:
            _inflight.pop(redis_key, None)


async def redis_catalog_cached_fetch(
    *,
    segment: str,
    logical_key: str,
    ttl_seconds: int,
    factory: Callable[[], Awaitable[T]],
    dumps: Callable[[T], bytes],
    loads: Callable[[bytes], T],
) -> T:
    """Return cached JSON-compatible payloads or load via ``factory`` (single-flight per key)."""

    global _catalog_cache_hits, _catalog_cache_misses, _catalog_cache_errors

    if settings.app.is_test:
        return await factory()

    client = await _redis()
    if client is None:
        return await factory()

    redis_key = bounded_cache_key(segment, logical_key)

    try:
        raw = await client.get(redis_key)
        if raw is not None:
            _catalog_cache_hits += 1
            logger.debug('catalog_cache hit segment=%s', segment)
            return loads(raw if isinstance(raw, (bytes, bytearray)) else bytes(raw))
    except Exception:
        logger.warning('catalog_cache get failed segment=%s', segment, exc_info=True)
        _catalog_cache_errors += 1

    _catalog_cache_misses += 1

    async with _inflight_lock:
        hit = None
        try:
            raw_retry = await client.get(redis_key)
            if raw_retry is not None:
                hit = (
                    raw_retry
                    if isinstance(raw_retry, (bytes, bytearray))
                    else bytes(raw_retry)
                )
        except Exception:
            logger.warning('catalog_cache double-get failed segment=%s', segment, exc_info=True)
            _catalog_cache_errors += 1

        if hit is not None:
            _catalog_cache_hits += 1
            _catalog_cache_misses -= 1
            return loads(hit)

        if redis_key not in _inflight:
            _inflight[redis_key] = asyncio.create_task(
                _run_factory_store(
                    client=client,
                    redis_key=redis_key,
                    ttl_seconds=ttl_seconds,
                    factory=factory,
                    dumps=dumps,
                ),
            )
        task = _inflight[redis_key]

    return await task
