"""In-process SSE broker for watch party rooms (MVP, single worker)."""

from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

import orjson

from conf import settings

_lock = asyncio.Lock()
_parties: dict[UUID, _PartyChannel] = {}


@dataclass
class _PartyChannel:
    seq: int = 0
    subscribers: set[asyncio.Queue[tuple[int, str, dict[str, Any]]]] = field(default_factory=set)


def reset_watch_party_broker_for_tests() -> None:
    _parties.clear()


async def publish_watch_party_event(
    party_id: UUID,
    *,
    event_type: str,
    payload: dict[str, Any],
) -> int:
    async with _lock:
        channel = _parties.setdefault(party_id, _PartyChannel())
        channel.seq += 1
        seq = channel.seq
        item = (seq, event_type, payload)
        for queue in list(channel.subscribers):
            try:
                queue.put_nowait(item)
            except Exception:
                continue
        return seq


async def iter_watch_party_sse(
    party_id: UUID,
    *,
    snapshot_payload: dict[str, Any],
    since_seq: int | None = None,
) -> AsyncIterator[bytes]:
    queue: asyncio.Queue[tuple[int, str, dict[str, Any]]] = asyncio.Queue(maxsize=64)
    async with _lock:
        channel = _parties.setdefault(party_id, _PartyChannel())
        channel.subscribers.add(queue)
        current_seq = channel.seq

    try:
        if since_seq is None or since_seq >= current_seq:
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
                if event_type == 'snapshot' and since_seq is not None and seq <= since_seq:
                    continue
                yield _encode_event(seq, event_type, payload)
    finally:
        async with _lock:
            channel = _parties.get(party_id)
            if channel is not None:
                channel.subscribers.discard(queue)


def _encode_event(seq: int, event_type: str, payload: dict[str, Any]) -> bytes:
    body = orjson.dumps({'seq': seq, 'type': event_type, 'payload': payload})
    return b'data: ' + body + b'\n\n'
