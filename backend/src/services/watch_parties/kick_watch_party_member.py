from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from daos.watch_party_dao import WatchPartyDAO
from models.watch_party_enums import WatchPartyMemberRole, WatchPartyMemberStatus
from services.watch_parties.ensure_active_watch_party import EnsureActiveWatchPartyService
from services.watch_parties.watch_party_redis import clear_user_watching


@dataclass
class KickWatchPartyMemberService:
    """Removes a guest from the party roster; host-only."""

    _dao: WatchPartyDAO
    _ensure_active: EnsureActiveWatchPartyService
    _session: AsyncSession

    class PartyNotFound(Exception):
        pass

    class PartyEnded(Exception):
        pass

    class HostRequired(Exception):
        pass

    class TargetNotFound(Exception):
        pass

    class CannotKickHost(Exception):
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
        target_user_id: UUID,
    ) -> None:
        try:
            party = await self._ensure_active.execute(party_id)
        except EnsureActiveWatchPartyService.PartyNotFound:
            raise self.PartyNotFound from None
        except EnsureActiveWatchPartyService.PartyEnded:
            raise self.PartyEnded from None

        if party.host_user_id != actor_user_id:
            raise self.HostRequired

        if target_user_id == party.host_user_id:
            raise self.CannotKickHost

        target = await self._dao.get_member(party_id=party.id, user_id=target_user_id)
        if target is None or target.status == WatchPartyMemberStatus.left:
            raise self.TargetNotFound

        if target.role == WatchPartyMemberRole.host:
            raise self.CannotKickHost

        await self._dao.update_member_status(
            party_id=party.id,
            user_id=target_user_id,
            status=WatchPartyMemberStatus.left,
        )
        await self._session.commit()
        await clear_user_watching(target_user_id)
