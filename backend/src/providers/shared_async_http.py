"""Shared httpx.AsyncClient and bounded-retries for idempotent GETs (provider calls)."""

from __future__ import annotations

import asyncio
import random
from http import HTTPStatus

import httpx

_client_lock = asyncio.Lock()
_shared_client: httpx.AsyncClient | None = None

# Granular timeouts vs a single blob: fast fail on connect; allow slower reads for large JSON.
_DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=30.0, write=15.0, pool=5.0)
_DEFAULT_LIMITS = httpx.Limits(max_keepalive_connections=32, max_connections=128)

_GET_MAX_ATTEMPTS = 5


async def get_shared_httpx_client() -> httpx.AsyncClient:
    """Process-wide AsyncClient (reuse TCP/TLS); safe to share across concurrent tasks."""
    global _shared_client
    async with _client_lock:
        if _shared_client is None:
            _shared_client = httpx.AsyncClient(
                timeout=_DEFAULT_TIMEOUT,
                limits=_DEFAULT_LIMITS,
            )
        return _shared_client


def _backoff_seconds(attempt: int, *, cap: float = 8.0) -> float:
    base = min(cap, 0.2 * (2**attempt))
    jitter = random.uniform(0, base * 0.2)
    return min(cap, base + jitter)


def _retry_after_seconds(response: httpx.Response) -> float | None:
    raw = response.headers.get('retry-after')
    if raw is None or raw.strip() == '':
        return None
    try:
        return float(raw)
    except ValueError:
        return None


async def httpx_get_idempotent(
    url: str,
    *,
    headers: dict[str, str] | None = None,
    params: dict[str, object] | None = None,
) -> httpx.Response:
    """GET with retry/backoff on transport errors, 429, and 5xx (idempotent)."""
    last_response: httpx.Response | None = None
    for attempt in range(_GET_MAX_ATTEMPTS):
        client = await get_shared_httpx_client()
        try:
            response = await client.get(url, headers=headers, params=params)
        except httpx.HTTPError:
            if attempt >= _GET_MAX_ATTEMPTS - 1:
                raise
            await asyncio.sleep(_backoff_seconds(attempt))
            continue

        last_response = response
        if response.status_code == HTTPStatus.TOO_MANY_REQUESTS:
            ra = _retry_after_seconds(response)
            delay = ra if ra is not None else _backoff_seconds(attempt)
            await asyncio.sleep(min(60.0, max(0.1, delay)))
            continue

        if HTTPStatus.INTERNAL_SERVER_ERROR <= response.status_code < 600:
            await asyncio.sleep(_backoff_seconds(attempt))
            continue

        return response

    if last_response is not None:
        return last_response
    msg = 'httpx_get_idempotent exhausted attempts without response'
    raise RuntimeError(msg)
