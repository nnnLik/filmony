"""Unit tests for watch party SSE broker."""

from __future__ import annotations

import asyncio
import json
from uuid import uuid4

import pytest

from services.watch_parties.watch_party_broker import (
    iter_watch_party_sse,
    publish_watch_party_event,
    reset_watch_party_broker_for_tests,
)


@pytest.mark.asyncio
async def test_publish_reaches_sse_subscriber() -> None:
    reset_watch_party_broker_for_tests()
    party_id = uuid4()
    snapshot = {'party_id': str(party_id), 'messages': []}

    async def consume() -> dict | None:
        async for chunk in iter_watch_party_sse(
            party_id,
            snapshot_payload=snapshot,
            since_seq=None,
        ):
            if not chunk.startswith(b'data: '):
                continue
            payload = json.loads(chunk.removeprefix(b'data: ').strip())
            if payload['type'] == 'playback_state':
                return payload
        return None

    task = asyncio.create_task(consume())
    await asyncio.sleep(0.05)
    await publish_watch_party_event(
        party_id,
        event_type='playback_state',
        payload={'playback_state': {'playing': True, 'position_ms': 42}},
    )
    result = await asyncio.wait_for(task, timeout=2.0)
    assert result is not None
    assert result['payload']['playback_state']['playing'] is True
