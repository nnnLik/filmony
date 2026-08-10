from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from conf import settings
from daos.watch_party_dao import WatchPartyDAO
from models.watch_party_enums import WatchPartyMemberStatus
from services.watch_parties.ensure_active_watch_party import EnsureActiveWatchPartyService
from services.watch_parties.watch_party_broker import publish_watch_party_event
from services.watch_parties.watch_party_redis import enforce_typing_rate_limit, set_typing


@dataclass
class RecordWatchPartyTypingService:
    """Records ephemeral typing state and broadcasts a typing SSE event."""

    _dao: WatchPartyDAO
    _ensure_active: EnsureActiveWatchPartyService

    class PartyNotFound(Exception):
        pass

    class PartyEnded(Exception):
        pass

    class NotMember(Exception):
        pass

    class RateLimited(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        dao = WatchPartyDAO(session)
        return cls(
            _dao=dao,
            _ensure_active=EnsureActiveWatchPartyService.build(dao),
        )

    async def execute(self, *, party_id: UUID, actor_user_id: UUID, display_name: str) -> None:
        try:
            party = await self._ensure_active.execute(party_id)
        except EnsureActiveWatchPartyService.PartyNotFound:
            raise self.PartyNotFound from None
        except EnsureActiveWatchPartyService.PartyEnded:
            raise self.PartyEnded from None

        member = await self._dao.get_member(party_id=party.id, user_id=actor_user_id)
        if member is None or member.status == WatchPartyMemberStatus.left:
            raise self.NotMember

        allowed = await enforce_typing_rate_limit(party.id, actor_user_id, window_seconds=2.0)
        if not allowed:
            raise self.RateLimited

        safe_name = (display_name or 'Пользователь').strip() or 'Пользователь'
        await set_typing(
            party.id,
            actor_user_id,
            safe_name,
            settings.watch_party.typing_ttl_seconds,
        )
        await publish_watch_party_event(
            party.id,
            event_type='typing',
            payload={'user_id': str(actor_user_id), 'display_name': safe_name},
        )
