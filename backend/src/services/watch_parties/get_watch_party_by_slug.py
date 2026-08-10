from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from daos.watch_party_dao import WatchPartyDAO
from services.watch_parties.ensure_active_watch_party import EnsureActiveWatchPartyService


@dataclass(frozen=True, slots=True)
class WatchPartySlugResolveDTO:
    party_id: UUID
    invite_slug: str
    status: str


@dataclass
class GetWatchPartyBySlugService:
    """Resolves an invite slug to a party id for join landing."""

    _dao: WatchPartyDAO
    _ensure_active: EnsureActiveWatchPartyService

    class PartyNotFound(Exception):
        pass

    class PartyEnded(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        dao = WatchPartyDAO(session)
        return cls(
            _dao=dao,
            _ensure_active=EnsureActiveWatchPartyService.build(dao),
        )

    async def execute(self, *, invite_slug: str) -> WatchPartySlugResolveDTO:
        party = await self._dao.get_party_by_slug(invite_slug)
        if party is None:
            raise self.PartyNotFound
        try:
            party = await self._ensure_active.execute(party.id)
        except EnsureActiveWatchPartyService.PartyEnded:
            raise self.PartyEnded from None
        return WatchPartySlugResolveDTO(
            party_id=party.id,
            invite_slug=party.invite_slug,
            status=party.status.value,
        )
