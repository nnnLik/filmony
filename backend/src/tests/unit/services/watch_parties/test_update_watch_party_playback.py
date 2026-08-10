"""Unit tests for watch party playback state transitions."""

from __future__ import annotations

import datetime as dt
from uuid import uuid4

import pytest

from services.watch_parties.update_watch_party_playback import UpdateWatchPartyPlaybackService


class FakeParty:
    def __init__(self, host_user_id):
        self.id = uuid4()
        self.host_user_id = host_user_id
        self.playback_state = {
            'playing': False,
            'position_ms': 0,
            'updated_at': dt.datetime.now(dt.UTC).isoformat(),
            'host_user_id': str(host_user_id),
            'version': 0,
        }


class FakeEnsureActive:
    def __init__(self, party: FakeParty) -> None:
        self._party = party

    async def execute(self, _party_id):
        return self._party


class FakeDAO:
    def __init__(self) -> None:
        self.state: dict | None = None

    async def update_playback_state(self, *, party_id: object, playback_state: dict) -> None:
        _ = party_id
        self.state = playback_state


class FakeSession:
    async def commit(self) -> None:
        return None


@pytest.mark.asyncio
async def test_playback_play_updates_state(monkeypatch: pytest.MonkeyPatch) -> None:
    host_id = uuid4()
    party = FakeParty(host_id)
    dao = FakeDAO()
    service = UpdateWatchPartyPlaybackService(
        _dao=dao,
        _ensure_active=FakeEnsureActive(party),
        _session=FakeSession(),
    )

    async def _noop_publish(*_args, **_kwargs):
        return 1

    monkeypatch.setattr(
        'services.watch_parties.update_watch_party_playback.publish_watch_party_event',
        _noop_publish,
    )

    state = await service.execute(
        party_id=party.id,
        actor_user_id=host_id,
        action='play',
        position_ms=1200,
    )
    assert state['playing'] is True
    assert state['position_ms'] == 1200
    assert state['version'] == 1


@pytest.mark.asyncio
async def test_playback_seek_rate_limited(monkeypatch: pytest.MonkeyPatch) -> None:
    host_id = uuid4()
    party = FakeParty(host_id)
    dao = FakeDAO()
    service = UpdateWatchPartyPlaybackService(
        _dao=dao,
        _ensure_active=FakeEnsureActive(party),
        _session=FakeSession(),
    )

    async def _noop_publish(*_args, **_kwargs):
        return 1

    async def _deny_seek(*_args, **_kwargs):
        return False

    monkeypatch.setattr(
        'services.watch_parties.update_watch_party_playback.publish_watch_party_event',
        _noop_publish,
    )
    monkeypatch.setattr(
        'services.watch_parties.update_watch_party_playback.enforce_seek_rate_limit',
        _deny_seek,
    )

    with pytest.raises(UpdateWatchPartyPlaybackService.SeekRateLimited):
        await service.execute(
            party_id=party.id,
            actor_user_id=host_id,
            action='seek',
            position_ms=5000,
        )


@pytest.mark.asyncio
async def test_playback_host_required() -> None:
    host_id = uuid4()
    guest_id = uuid4()
    party = FakeParty(host_id)
    dao = FakeDAO()
    service = UpdateWatchPartyPlaybackService(
        _dao=dao,
        _ensure_active=FakeEnsureActive(party),
        _session=FakeSession(),
    )

    with pytest.raises(UpdateWatchPartyPlaybackService.HostRequired):
        await service.execute(
            party_id=party.id,
            actor_user_id=guest_id,
            action='pause',
            position_ms=100,
        )
