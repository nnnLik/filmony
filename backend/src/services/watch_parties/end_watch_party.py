from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from daos.watch_party_dao import WatchPartyDAO
from models.watch_party_enums import WatchPartyStatus
from services.watch_parties.ensure_active_watch_party import EnsureActiveWatchPartyService
from services.watch_parties.watch_party_broker import publish_watch_party_event


@dataclass
class EndWatchPartyService:
    """Ends a watch party; host-only in MVP."""

    _dao: WatchPartyDAO
    _ensure_active: EnsureActiveWatchPartyService
    _session: AsyncSession

    class PartyNotFound(Exception):
        pass

    class PartyEnded(Exception):
        pass

    class HostRequired(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        dao = WatchPartyDAO(session)
        return cls(
            _dao=dao,
            _ensure_active=EnsureActiveWatchPartyService.build(dao),
            _session=session,
        )

    async def execute(self, *, party_id: UUID, actor_user_id: UUID) -> None:
        try:
            party = await self._ensure_active.execute(party_id)
        except EnsureActiveWatchPartyService.PartyNotFound:
            raise self.PartyNotFound from None
        except EnsureActiveWatchPartyService.PartyEnded:
            raise self.PartyEnded from None

        if party.host_user_id != actor_user_id:
            raise self.HostRequired

        await self._dao.update_party_status(
            party_id=party.id,
            status=WatchPartyStatus.ended,
            ended_at=dt.datetime.now(dt.UTC),
        )
        await self._session.commit()
        await publish_watch_party_event(
            party.id,
            event_type='party_ended',
            payload={},
        )
