from __future__ import annotations

import asyncio
import json
import time
from collections import defaultdict
from collections.abc import AsyncIterator
from typing import Any
from uuid import UUID

import orjson
from redis.asyncio import Redis

from conf import settings

_redis_client: Redis | None = None
_client_lock = asyncio.Lock()

_fake_seq: dict[str, int] = {}
_fake_pubsub: dict[str, list[asyncio.Queue[tuple[int, str, dict[str, Any]]]]] = defaultdict(list)
_fake_chat: dict[str, list[dict[str, Any]]] = {}
_fake_chat_id: dict[str, int] = {}
_fake_seek_rl: dict[str, list[float]] = {}
_fake_message_rl: dict[str, list[float]] = {}
_fake_typing: dict[str, dict[str, Any]] = {}
_fake_user_watching: dict[str, dict[str, Any]] = {}
_fake_typing_rl: dict[str, float] = {}


def _party_key(party_id: UUID) -> str:
    return str(party_id)


def _events_channel(party_id: UUID) -> str:
    return f'watch_party:events:{party_id}'


def _seq_key(party_id: UUID) -> str:
    return f'watch_party:seq:{party_id}'


def _chat_key(party_id: UUID) -> str:
    return f'watch_party:chat:{party_id}'


def _chat_id_key(party_id: UUID) -> str:
    return f'watch_party:chat_id:{party_id}'


def _seek_rl_key(party_id: UUID, user_id: UUID) -> str:
    return f'watch_party:seek_rl:{party_id}:{user_id}'


def _message_rl_key(party_id: UUID, user_id: UUID) -> str:
    return f'watch_party:message_rl:{party_id}:{user_id}'


def _typing_key(party_id: UUID, user_id: UUID) -> str:
    return f'watch_party:typing:{party_id}:{user_id}'


def _typing_rl_key(party_id: UUID, user_id: UUID) -> str:
    return f'watch_party:typing_rl:{party_id}:{user_id}'


def _user_watching_key(user_id: UUID) -> str:
    return f'watch_party:user_watching:{user_id}'


def watch_party_redis_url() -> str | None:
    raw = (settings.watch_party.redis_url or '').strip()
    if raw:
        return raw
    catalog = (settings.catalog_cache.redis_url or '').strip()
    if catalog:
        return catalog
    broker = settings.celery.broker_url.strip()
    if broker.startswith(('redis://', 'rediss://')):
        return broker
    return None


def _use_fake() -> bool:
    return settings.app.is_test


def _memory_only() -> bool:
    return _use_fake() or watch_party_redis_url() is None


async def get_redis() -> Redis | None:
    if _use_fake():
        return None
    global _redis_client
    url = watch_party_redis_url()
    if url is None:
        return None
    if _redis_client is not None:
        return _redis_client
    async with _client_lock:
        if _redis_client is None:
            _redis_client = Redis.from_url(url, decode_responses=False)
    return _redis_client


def reset_watch_party_redis_for_tests() -> None:
    _fake_seq.clear()
    _fake_pubsub.clear()
    _fake_chat.clear()
    _fake_chat_id.clear()
    _fake_seek_rl.clear()
    _fake_message_rl.clear()
    _fake_typing.clear()
    _fake_user_watching.clear()
    _fake_typing_rl.clear()


async def _incr_seq(party_id: UUID) -> int:
    if _memory_only():
        key = _party_key(party_id)
        _fake_seq[key] = _fake_seq.get(key, 0) + 1
        return _fake_seq[key]
    client = await get_redis()
    assert client is not None
    return int(await client.incr(_seq_key(party_id)))


def _fanout_fake(party_id: UUID, item: tuple[int, str, dict[str, Any]]) -> None:
    for queue in list(_fake_pubsub.get(_party_key(party_id), [])):
        try:
            queue.put_nowait(item)
        except Exception:
            continue


async def publish_party_event(
    party_id: UUID,
    event_type: str,
    payload: dict[str, Any],
) -> int:
    seq = await _incr_seq(party_id)
    envelope = {'seq': seq, 'type': event_type, 'payload': payload}
    if _memory_only():
        _fanout_fake(party_id, (seq, event_type, payload))
        return seq
    client = await get_redis()
    assert client is not None
    await client.publish(_events_channel(party_id), orjson.dumps(envelope))
    return seq


async def subscribe_party_events(
    party_id: UUID,
) -> AsyncIterator[tuple[int, str, dict[str, Any]]]:
    if _memory_only():
        queue: asyncio.Queue[tuple[int, str, dict[str, Any]]] = asyncio.Queue(maxsize=256)
        key = _party_key(party_id)
        _fake_pubsub[key].append(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            subs = _fake_pubsub.get(key, [])
            if queue in subs:
                subs.remove(queue)
        return

    client = await get_redis()
    assert client is not None

    pubsub = client.pubsub()
    await pubsub.subscribe(_events_channel(party_id))
    try:
        while True:
            message = await pubsub.get_message(ignore_subscribe_messages=True, timeout=1.0)
            if message is None or message.get('type') != 'message':
                await asyncio.sleep(0)
                continue
            data = message.get('data')
            if not isinstance(data, (bytes, bytearray)):
                continue
            parsed = orjson.loads(data)
            yield (
                int(parsed['seq']),
                str(parsed['type']),
                dict(parsed['payload']),
            )
    finally:
        await pubsub.unsubscribe(_events_channel(party_id))
        await pubsub.aclose()


async def append_chat_message(
    party_id: UUID,
    *,
    author_user_id: UUID,
    body: str,
    created_at: str,
) -> dict[str, Any]:
    max_messages = settings.watch_party.chat_max_messages
    if _memory_only():
        pid = _party_key(party_id)
        msg_id = _fake_chat_id.get(pid, 0) + 1
        _fake_chat_id[pid] = msg_id
        record = {
            'id': msg_id,
            'author_user_id': str(author_user_id),
            'body': body,
            'created_at': created_at,
        }
        _fake_chat.setdefault(pid, []).append(record)
        if len(_fake_chat[pid]) > max_messages:
            _fake_chat[pid] = _fake_chat[pid][-max_messages:]
        return record

    client = await get_redis()
    assert client is not None

    msg_id = int(await client.incr(_chat_id_key(party_id)))
    record = {
        'id': msg_id,
        'author_user_id': str(author_user_id),
        'body': body,
        'created_at': created_at,
    }
    chat_key = _chat_key(party_id)
    await client.lpush(chat_key, orjson.dumps(record))
    await client.ltrim(chat_key, 0, max_messages - 1)
    return record


async def list_chat_messages(
    party_id: UUID,
    *,
    before_id: int | None,
    limit: int,
) -> list[dict[str, Any]]:
    capped = min(max(limit, 1), settings.watch_party.chat_page_size)
    if _memory_only():
        messages = list(_fake_chat.get(_party_key(party_id), []))
        if before_id is not None:
            messages = [m for m in messages if int(m['id']) < before_id]
        messages.sort(key=lambda m: int(m['id']))
        return messages[-capped:]

    client = await get_redis()
    assert client is not None

    raw_items = await client.lrange(_chat_key(party_id), 0, -1)
    messages: list[dict[str, Any]] = []
    for raw in raw_items:
        if isinstance(raw, (bytes, bytearray)):
            messages.append(orjson.loads(raw))
        else:
            messages.append(json.loads(str(raw)))
    if before_id is not None:
        messages = [m for m in messages if int(m['id']) < before_id]
    messages.sort(key=lambda m: int(m['id']))
    return messages[-capped:]


async def delete_chat_message(party_id: UUID, message_id: int) -> bool:
    if _memory_only():
        pid = _party_key(party_id)
        items = _fake_chat.get(pid, [])
        kept = [m for m in items if int(m['id']) != message_id]
        if len(kept) == len(items):
            return False
        _fake_chat[pid] = kept
        return True

    client = await get_redis()
    assert client is not None

    raw_items = await client.lrange(_chat_key(party_id), 0, -1)
    removed = False
    for raw in raw_items:
        parsed = orjson.loads(raw) if isinstance(raw, (bytes, bytearray)) else json.loads(str(raw))
        if int(parsed['id']) == message_id:
            await client.lrem(_chat_key(party_id), 1, raw)
            removed = True
            break
    return removed


async def _sliding_window_count(
    *,
    key: str,
    window_seconds: int,
    limit: int,
    fake_bucket: dict[str, list[float]],
) -> bool:
    now = time.time()
    window_start = now - window_seconds
    if _memory_only():
        recent = [ts for ts in fake_bucket.get(key, []) if ts >= window_start]
        if len(recent) >= limit:
            return False
        recent.append(now)
        fake_bucket[key] = recent
        return True

    client = await get_redis()
    assert client is not None
    await client.zremrangebyscore(key, 0, window_start)
    count = await client.zcard(key)
    if int(count) >= limit:
        return False
    await client.zadd(key, {str(now): now})
    await client.expire(key, window_seconds + 5)
    return True


async def enforce_seek_rate_limit(
    party_id: UUID,
    user_id: UUID,
    limit: int,
    *,
    window_seconds: int = 60,
) -> bool:
    key = _seek_rl_key(party_id, user_id)
    return await _sliding_window_count(
        key=key,
        window_seconds=window_seconds,
        limit=limit,
        fake_bucket=_fake_seek_rl,
    )


async def enforce_message_rate_limit(
    party_id: UUID,
    user_id: UUID,
    limit: int = 20,
    *,
    window_seconds: int = 60,
) -> bool:
    key = _message_rl_key(party_id, user_id)
    return await _sliding_window_count(
        key=key,
        window_seconds=window_seconds,
        limit=limit,
        fake_bucket=_fake_message_rl,
    )


async def enforce_typing_rate_limit(
    party_id: UUID,
    user_id: UUID,
    *,
    window_seconds: float = 2.0,
) -> bool:
    key = _typing_rl_key(party_id, user_id)
    now = time.time()
    if _memory_only():
        last = _fake_typing_rl.get(key)
        if last is not None and now - last < window_seconds:
            return False
        _fake_typing_rl[key] = now
        return True
    client = await get_redis()
    assert client is not None
    acquired = await client.set(key, b'1', nx=True, ex=int(window_seconds) + 1)
    return bool(acquired)


async def set_typing(
    party_id: UUID,
    user_id: UUID,
    display_name: str,
    ttl: int,
) -> None:
    payload = {'user_id': str(user_id), 'display_name': display_name}
    if _memory_only():
        _fake_typing[_typing_key(party_id, user_id)] = payload
        return
    client = await get_redis()
    assert client is not None
    await client.set(_typing_key(party_id, user_id), orjson.dumps(payload), ex=ttl)


async def list_typing(party_id: UUID) -> list[dict[str, Any]]:
    prefix = f'watch_party:typing:{party_id}:'
    if _memory_only():
        out: list[dict[str, Any]] = []
        for key, value in _fake_typing.items():
            if key.startswith(prefix):
                out.append(dict(value))
        return out
    client = await get_redis()
    assert client is not None
    keys = [k async for k in client.scan_iter(match=f'{prefix}*')]
    if not keys:
        return []
    values = await client.mget(keys)
    result: list[dict[str, Any]] = []
    for raw in values:
        if raw is None:
            continue
        parsed = orjson.loads(raw) if isinstance(raw, (bytes, bytearray)) else json.loads(str(raw))
        result.append(dict(parsed))
    return result


async def set_user_watching(
    user_id: UUID,
    payload: dict[str, Any],
    *,
    ttl_seconds: int,
) -> None:
    if _memory_only():
        _fake_user_watching[_user_watching_key(user_id)] = dict(payload)
        return
    client = await get_redis()
    assert client is not None
    await client.set(
        _user_watching_key(user_id),
        orjson.dumps(payload),
        ex=ttl_seconds,
    )


async def clear_user_watching(user_id: UUID) -> None:
    if _memory_only():
        _fake_user_watching.pop(_user_watching_key(user_id), None)
        return
    client = await get_redis()
    assert client is not None
    await client.delete(_user_watching_key(user_id))


async def batch_user_watching(user_ids: list[UUID]) -> dict[UUID, dict[str, Any]]:
    unique = list(dict.fromkeys(user_ids))
    if not unique:
        return {}
    if _memory_only():
        out: dict[UUID, dict[str, Any]] = {}
        for uid in unique:
            raw = _fake_user_watching.get(_user_watching_key(uid))
            if raw is not None:
                out[uid] = dict(raw)
        return out
    client = await get_redis()
    assert client is not None
    keys = [_user_watching_key(uid) for uid in unique]
    values = await client.mget(keys)
    out = {}
    for uid, raw in zip(unique, values, strict=True):
        if raw is None:
            continue
        parsed = orjson.loads(raw) if isinstance(raw, (bytes, bytearray)) else json.loads(str(raw))
        out[uid] = dict(parsed)
    return out


async def clear_party_redis(party_id: UUID, member_user_ids: list[UUID]) -> None:
    if _memory_only():
        pid = _party_key(party_id)
        _fake_seq.pop(pid, None)
        _fake_pubsub.pop(pid, None)
        _fake_chat.pop(pid, None)
        _fake_chat_id.pop(pid, None)
        keys_to_drop = [
            k for k in list(_fake_seek_rl) if k.startswith(f'watch_party:seek_rl:{party_id}:')
        ]
        for k in keys_to_drop:
            _fake_seek_rl.pop(k, None)
        keys_to_drop = [
            k for k in list(_fake_message_rl) if k.startswith(f'watch_party:message_rl:{party_id}:')
        ]
        for k in keys_to_drop:
            _fake_message_rl.pop(k, None)
        typing_prefix = f'watch_party:typing:{party_id}:'
        for k in list(_fake_typing):
            if k.startswith(typing_prefix):
                _fake_typing.pop(k, None)
        for uid in member_user_ids:
            _fake_user_watching.pop(_user_watching_key(uid), None)
        return

    client = await get_redis()
    assert client is not None
    await client.delete(
        _seq_key(party_id),
        _chat_key(party_id),
        _chat_id_key(party_id),
    )
    async for key in client.scan_iter(match=f'watch_party:seek_rl:{party_id}:*'):
        await client.delete(key)
    async for key in client.scan_iter(match=f'watch_party:message_rl:{party_id}:*'):
        await client.delete(key)
    async for key in client.scan_iter(match=f'watch_party:typing:{party_id}:*'):
        await client.delete(key)
    if member_user_ids:
        await client.delete(*[_user_watching_key(uid) for uid in member_user_ids])
