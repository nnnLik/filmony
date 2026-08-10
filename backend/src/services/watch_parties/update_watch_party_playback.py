from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Literal, Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from daos.watch_party_dao import WatchPartyDAO
from services.watch_parties.ensure_active_watch_party import EnsureActiveWatchPartyService
from services.watch_parties.watch_party_broker import publish_watch_party_event

PlaybackAction = Literal['play', 'pause', 'seek']


@dataclass
class UpdateWatchPartyPlaybackService:
    """Applies host playback commands and broadcasts updated state."""

    _dao: WatchPartyDAO
    _ensure_active: EnsureActiveWatchPartyService
    _session: AsyncSession
    _seek_timestamps: dict[tuple[UUID, UUID], list[dt.datetime]]

    class PartyNotFound(Exception):
        pass

    class PartyEnded(Exception):
        pass

    class HostRequired(Exception):
        pass

    class InvalidAction(Exception):
        pass

    class SeekRateLimited(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        dao = WatchPartyDAO(session)
        return cls(
            _dao=dao,
            _ensure_active=EnsureActiveWatchPartyService.build(dao),
            _session=session,
            _seek_timestamps={},
        )

    async def execute(
        self,
        *,
        party_id: UUID,
        actor_user_id: UUID,
        action: PlaybackAction,
        position_ms: int | None = None,
    ) -> dict:
        try:
            party = await self._ensure_active.execute(party_id)
        except EnsureActiveWatchPartyService.PartyNotFound:
            raise self.PartyNotFound from None
        except EnsureActiveWatchPartyService.PartyEnded:
            raise self.PartyEnded from None

        if party.host_user_id != actor_user_id:
            raise self.HostRequired

        state = dict(party.playback_state or {})
        now = dt.datetime.now(dt.UTC)
        now_iso = now.isoformat()
        current_position = int(state.get('position_ms', 0))

        if action == 'play':
            state['playing'] = True
            if position_ms is not None:
                state['position_ms'] = max(0, position_ms)
        elif action == 'pause':
            state['playing'] = False
            state['position_ms'] = max(
                0, position_ms if position_ms is not None else current_position
            )
        elif action == 'seek':
            if position_ms is None:
                raise self.InvalidAction
            self._enforce_seek_rate_limit(party_id=party.id, actor_user_id=actor_user_id, now=now)
            state['position_ms'] = max(0, position_ms)
            state['playing'] = bool(state.get('playing', False))
        else:
            raise self.InvalidAction

        state['updated_at'] = now_iso
        state['host_user_id'] = str(party.host_user_id)
        state['version'] = int(state.get('version', 0)) + 1

        await self._dao.update_playback_state(party_id=party.id, playback_state=state)
        await self._session.commit()

        await publish_watch_party_event(
            party.id,
            event_type='playback_state',
            payload={'playback_state': state},
        )
        return state

    def _enforce_seek_rate_limit(
        self,
        *,
        party_id: UUID,
        actor_user_id: UUID,
        now: dt.datetime,
    ) -> None:
        key = (party_id, actor_user_id)
        window_start = now - dt.timedelta(minutes=1)
        recent = [ts for ts in self._seek_timestamps.get(key, []) if ts >= window_start]
        if len(recent) >= 10:
            raise self.SeekRateLimited
        recent.append(now)
        self._seek_timestamps[key] = recent
