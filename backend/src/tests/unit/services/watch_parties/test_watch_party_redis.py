"""Unit tests for watch party Redis helpers."""

from __future__ import annotations

from uuid import uuid4

import pytest

from services.watch_parties.watch_party_redis import (
    append_chat_message,
    batch_user_watching,
    clear_party_redis,
    enforce_message_rate_limit,
    enforce_seek_rate_limit,
    list_chat_messages,
    publish_party_event,
    reset_watch_party_redis_for_tests,
    set_user_watching,
    subscribe_party_events,
)


@pytest.fixture(autouse=True)
def _reset_redis() -> None:
    reset_watch_party_redis_for_tests()


@pytest.mark.asyncio
async def test_chat_append_and_list() -> None:
    party_id = uuid4()
    user_id = uuid4()
    saved = await append_chat_message(
        party_id,
        author_user_id=user_id,
        body='hello',
        created_at='2026-08-11T00:00:00+00:00',
    )
    assert saved['body'] == 'hello'
    listed = await list_chat_messages(party_id, before_id=None, limit=10)
    assert len(listed) == 1
    assert listed[0]['id'] == saved['id']


@pytest.mark.asyncio
async def test_publish_subscribe_fanout() -> None:
    party_id = uuid4()

    async def collect_one() -> tuple[int, str, dict]:
        async for item in subscribe_party_events(party_id):
            return item
        raise AssertionError('no event')

    import asyncio

    task = asyncio.create_task(collect_one())
    await asyncio.sleep(0.05)
    seq = await publish_party_event(party_id, 'playback_state', {'playing': True})
    event = await asyncio.wait_for(task, timeout=2.0)
    assert event[0] == seq
    assert event[1] == 'playback_state'


@pytest.mark.asyncio
async def test_seek_rate_limit_blocks_after_limit() -> None:
    party_id = uuid4()
    user_id = uuid4()
    for _ in range(10):
        assert await enforce_seek_rate_limit(party_id, user_id, 10, window_seconds=60)
    assert not await enforce_seek_rate_limit(party_id, user_id, 10, window_seconds=60)


@pytest.mark.asyncio
async def test_user_watching_batch() -> None:
    user_id = uuid4()
    await set_user_watching(
        user_id,
        {'film_id': 42, 'film_title': 'Test', 'party_id': str(uuid4())},
        ttl_seconds=60,
    )
    result = await batch_user_watching([user_id])
    assert user_id in result
    assert result[user_id]['film_id'] == 42


@pytest.mark.asyncio
async def test_clear_party_redis() -> None:
    party_id = uuid4()
    user_id = uuid4()
    await append_chat_message(
        party_id,
        author_user_id=user_id,
        body='x',
        created_at='2026-08-11T00:00:00+00:00',
    )
    await set_user_watching(user_id, {'film_id': 1, 'film_title': 'A'}, ttl_seconds=60)
    await clear_party_redis(party_id, [user_id])
    assert await list_chat_messages(party_id, before_id=None, limit=10) == []
    assert await batch_user_watching([user_id]) == {}


@pytest.mark.asyncio
async def test_message_rate_limit() -> None:
    party_id = uuid4()
    user_id = uuid4()
    for _ in range(20):
        assert await enforce_message_rate_limit(party_id, user_id, 20, window_seconds=60)
    assert not await enforce_message_rate_limit(party_id, user_id, 20, window_seconds=60)
