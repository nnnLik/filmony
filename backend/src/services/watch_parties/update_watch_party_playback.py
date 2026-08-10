from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Literal, Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from conf import settings
from daos.watch_party_dao import WatchPartyDAO
from services.watch_parties.ensure_active_watch_party import EnsureActiveWatchPartyService
from services.watch_parties.helpers import expected_playback_ms
from services.watch_parties.watch_party_broker import publish_watch_party_event
from services.watch_parties.watch_party_redis import enforce_seek_rate_limit

PlaybackAction = Literal['play', 'pause', 'seek']


@dataclass
class UpdateWatchPartyPlaybackService:
    """Applies host playback commands and broadcasts updated state."""

    _dao: WatchPartyDAO
    _ensure_active: EnsureActiveWatchPartyService
    _session: AsyncSession

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

        if state.get('playing'):
            current_position = expected_playback_ms(state, now=now)
        else:
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
            allowed = await enforce_seek_rate_limit(
                party.id,
                actor_user_id,
                settings.watch_party.seek_rate_limit,
                window_seconds=60,
            )
            if not allowed:
                raise self.SeekRateLimited
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
