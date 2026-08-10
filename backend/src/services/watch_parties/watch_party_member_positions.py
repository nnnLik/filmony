from __future__ import annotations

import datetime as dt
from typing import Any
from uuid import UUID

from conf import settings
from daos.watch_party_dao import WatchPartyMemberRow
from models.watch_party import WatchParty
from services.watch_parties.watch_party_redis import batch_member_positions, set_member_position


def member_position_ttl_seconds() -> int:
    interval = settings.watch_party.heartbeat_interval_seconds
    left = settings.watch_party.missed_heartbeats_left
    return interval * left + interval


async def build_member_payloads(
    *,
    party: WatchParty,
    member_rows: list[WatchPartyMemberRow],
) -> list[dict[str, Any]]:
    stored = await batch_member_positions(party.id, [row.user_id for row in member_rows])
    playback = party.playback_state or {}
    host_id = party.host_user_id

    payloads: list[dict[str, Any]] = []
    for row in member_rows:
        payload: dict[str, Any] = {
            'user_id': str(row.user_id),
            'display_name': row.display_name or 'Пользователь',
            'photo_url': row.photo_url,
            'role': row.role,
            'status': row.status,
            'joined_at': row.joined_at.isoformat(),
        }
        if row.user_id == host_id:
            payload['position_ms'] = int(playback.get('position_ms', 0))
            payload['position_playing'] = bool(playback.get('playing', False))
            payload['position_at'] = str(playback.get('updated_at', ''))
        else:
            pos = stored.get(row.user_id)
            if pos is not None:
                payload['position_ms'] = int(pos['position_ms'])
                payload['position_playing'] = bool(pos.get('playing', False))
                payload['position_at'] = str(pos.get('position_at', ''))
            else:
                payload['position_ms'] = None
                payload['position_playing'] = None
                payload['position_at'] = None
        payloads.append(payload)
    return payloads


async def persist_member_position(
    *,
    party_id: UUID,
    user_id: UUID,
    position_ms: int,
    playing: bool,
) -> dict[str, Any]:
    position_at = dt.datetime.now(dt.UTC).isoformat()
    payload = {
        'position_ms': max(0, position_ms),
        'playing': playing,
        'position_at': position_at,
    }
    await set_member_position(
        party_id,
        user_id,
        payload,
        ttl_seconds=member_position_ttl_seconds(),
    )
    return {
        'user_id': str(user_id),
        'position_ms': payload['position_ms'],
        'position_playing': playing,
        'position_at': position_at,
    }
