from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from daos.watch_party_dao import WatchPartyDAO
from models.watch_party_enums import WatchPartyStatus
from services.watch_parties.watch_party_broker import publish_watch_party_event
from services.watch_parties.watch_party_redis import clear_party_redis, clear_user_watching


@dataclass
class EndExpiredWatchPartiesService:
    """Ends watch parties past TTL and clears ephemeral Redis state."""

    _dao: WatchPartyDAO
    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_dao=WatchPartyDAO(session), _session=session)

    async def execute(self, *, now: dt.datetime | None = None) -> int:
        current = now or dt.datetime.now(dt.UTC)
        expired = await self._dao.list_expired_active_parties(now=current)
        ended_count = 0
        for party in expired:
            member_rows = await self._dao.list_member_rows(party.id)
            member_user_ids = [row.user_id for row in member_rows]
            await self._dao.update_party_status(
                party_id=party.id,
                status=WatchPartyStatus.ended,
                ended_at=current,
            )
            ended_count += 1
            await publish_watch_party_event(
                party.id,
                event_type='party_ended',
                payload={},
            )
            await clear_party_redis(party.id, member_user_ids)
            for user_id in member_user_ids:
                await clear_user_watching(user_id)
        if ended_count:
            await self._session.commit()
        return ended_count
