from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from conf import settings
from daos.watch_party_dao import WatchPartyDAO
from models.watch_party import WatchParty
from models.watch_party_enums import WatchPartyStatus


@dataclass(frozen=True, slots=True)
class ActivePartyConflict:
    active_party_id: UUID
    invite_slug: str


def _as_utc(value: dt.datetime) -> dt.datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=dt.UTC)
    return value.astimezone(dt.UTC)


def party_ttl_deadline(party: WatchParty) -> dt.datetime:
    return _as_utc(party.created_at) + dt.timedelta(hours=settings.watch_party.ttl_hours)


def is_party_expired(party: WatchParty, *, now: dt.datetime | None = None) -> bool:
    current = now or dt.datetime.now(dt.UTC)
    return current >= party_ttl_deadline(party)


@dataclass
class EnsureActiveWatchPartyService:
    """Loads an active party or ends it when TTL elapsed."""

    _dao: WatchPartyDAO

    class PartyNotFound(Exception):
        pass

    class PartyEnded(Exception):
        pass

    @classmethod
    def build(cls, dao: WatchPartyDAO) -> Self:
        return cls(_dao=dao)

    async def execute(self, party_id: UUID) -> WatchParty:
        party = await self._dao.get_party_by_id(party_id)
        if party is None:
            raise self.PartyNotFound
        if party.status == WatchPartyStatus.ended:
            raise self.PartyEnded
        if is_party_expired(party):
            await self._dao.update_party_status(
                party_id=party.id,
                status=WatchPartyStatus.ended,
                ended_at=dt.datetime.now(dt.UTC),
            )
            raise self.PartyEnded
        return party
