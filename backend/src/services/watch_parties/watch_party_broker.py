from __future__ import annotations

import asyncio
import contextlib
from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

import orjson

from conf import settings
from services.watch_parties.watch_party_redis import (
    publish_party_event,
    reset_watch_party_redis_for_tests,
    subscribe_party_events,
)


def reset_watch_party_broker_for_tests() -> None:
    reset_watch_party_redis_for_tests()


async def publish_watch_party_event(
    party_id: UUID,
    *,
    event_type: str,
    payload: dict[str, Any],
) -> int:
    return await publish_party_event(party_id, event_type, payload)


async def iter_watch_party_sse(
    party_id: UUID,
    *,
    snapshot_payload: dict[str, Any],
    since_seq: int | None = None,
) -> AsyncIterator[bytes]:
    queue: asyncio.Queue[tuple[int, str, dict[str, Any]]] = asyncio.Queue(maxsize=64)
    stop_event = asyncio.Event()

    async def _redis_listener() -> None:
        try:
            async for item in subscribe_party_events(party_id):
                if stop_event.is_set():
                    break
                try:
                    queue.put_nowait(item)
                except Exception:
                    continue
        except asyncio.CancelledError:
            raise
        except Exception:
            return

    listener = asyncio.create_task(_redis_listener())

    try:
        if since_seq is None:
            snapshot_seq = await publish_watch_party_event(
                party_id,
                event_type='snapshot',
                payload=snapshot_payload,
            )
            yield _encode_event(snapshot_seq, 'snapshot', snapshot_payload)
        ping_s = 2.0 if settings.app.is_test else float(settings.watch_party.sse_ping_seconds)
        while True:
            try:
                seq, event_type, payload = await asyncio.wait_for(queue.get(), timeout=ping_s)
            except TimeoutError:
                yield b': ping\n\n'
            else:
                if event_type == 'snapshot' and since_seq is None:
                    continue
                if event_type == 'snapshot' and since_seq is not None and seq <= since_seq:
                    continue
                if since_seq is not None and seq <= since_seq:
                    continue
                yield _encode_event(seq, event_type, payload)
    finally:
        stop_event.set()
        listener.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await listener


def _encode_event(seq: int, event_type: str, payload: dict[str, Any]) -> bytes:
    body = orjson.dumps({'seq': seq, 'type': event_type, 'payload': payload})
    return b'data: ' + body + b'\n\n'
