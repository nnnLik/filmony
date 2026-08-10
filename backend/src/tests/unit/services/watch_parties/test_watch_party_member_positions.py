"""Unit tests for watch party member position helpers."""

from __future__ import annotations

import datetime as dt
from uuid import uuid4

import pytest

from services.watch_parties.helpers import expected_playback_ms
from services.watch_parties.watch_party_member_positions import persist_member_position
from services.watch_parties.watch_party_redis import (
    batch_member_positions,
    reset_watch_party_redis_for_tests,
)


@pytest.fixture(autouse=True)
def _reset_redis() -> None:
    reset_watch_party_redis_for_tests()


def test_expected_playback_ms_paused() -> None:
    state = {
        'playing': False,
        'position_ms': 12_000,
        'updated_at': dt.datetime.now(dt.UTC).isoformat(),
    }
    assert expected_playback_ms(state) == 12_000


def test_expected_playback_ms_playing_extrapolates() -> None:
    updated_at = (dt.datetime.now(dt.UTC) - dt.timedelta(seconds=5)).isoformat()
    state = {
        'playing': True,
        'position_ms': 10_000,
        'updated_at': updated_at,
    }
    result = expected_playback_ms(state)
    assert result >= 14_500
    assert result <= 15_500


@pytest.mark.asyncio
async def test_persist_and_batch_member_position() -> None:
    party_id = uuid4()
    user_id = uuid4()
    payload = await persist_member_position(
        party_id=party_id,
        user_id=user_id,
        position_ms=42_000,
        playing=True,
    )
    assert payload['position_ms'] == 42_000
    assert payload['position_playing'] is True

    stored = await batch_member_positions(party_id, [user_id])
    assert stored[user_id]['position_ms'] == 42_000
    assert stored[user_id]['playing'] is True
