from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from conf import settings
from daos.watch_party_dao import WatchPartyDAO
from models.watch_party_enums import WatchPartyMemberStatus
from services.telegram.send_watch_party_invite_notification import (
    SendWatchPartyInviteNotificationService,
)
from services.watch_parties.ensure_active_watch_party import EnsureActiveWatchPartyService
from services.watchlist.assert_mutual_watch_partner import AssertMutualWatchPartnerService


@dataclass
class InviteWatchPartyMembersService:
    """Invites mutual follows to join an active watch party."""

    _dao: WatchPartyDAO
    _ensure_active: EnsureActiveWatchPartyService
    _mutual: AssertMutualWatchPartnerService
    _notify: SendWatchPartyInviteNotificationService

    class PartyNotFound(Exception):
        pass

    class PartyEnded(Exception):
        pass

    class HostRequired(Exception):
        pass

    class PartyFull(Exception):
        pass

    class InvalidTarget(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        dao = WatchPartyDAO(session)
        return cls(
            _dao=dao,
            _ensure_active=EnsureActiveWatchPartyService.build(dao),
            _mutual=AssertMutualWatchPartnerService.build(session),
            _notify=SendWatchPartyInviteNotificationService.build(),
        )

    async def execute(
        self,
        *,
        party_id: UUID,
        actor_user_id: UUID,
        user_ids: list[UUID],
    ) -> int:
        try:
            party = await self._ensure_active.execute(party_id)
        except EnsureActiveWatchPartyService.PartyNotFound:
            raise self.PartyNotFound from None
        except EnsureActiveWatchPartyService.PartyEnded:
            raise self.PartyEnded from None

        if party.host_user_id != actor_user_id:
            raise self.HostRequired

        unique_targets = list(dict.fromkeys(user_ids))
        if not unique_targets:
            return 0

        roster = await self._dao.list_member_rows(party.id)
        active_count = sum(
            1
            for row in roster
            if row.status
            in (WatchPartyMemberStatus.active.value, WatchPartyMemberStatus.away.value)
        )
        max_members = party.max_members or settings.watch_party.hard_max_members
        roster_user_ids = {row.user_id for row in roster}

        sent = 0
        for target_user_id in unique_targets:
            if target_user_id in roster_user_ids:
                continue
            if active_count + sent >= max_members:
                raise self.PartyFull
            try:
                await self._mutual.execute(
                    actor_user_id=actor_user_id,
                    watch_with_user_id=target_user_id,
                )
            except AssertMutualWatchPartnerService.WatchWithUserNotFoundError:
                raise self.InvalidTarget from None
            except AssertMutualWatchPartnerService.NotMutualWatchPartnerError:
                raise self.InvalidTarget from None

            await self._notify.execute(
                actor_user_id=actor_user_id,
                invited_user_id=target_user_id,
                party_id=party.id,
                invite_slug=party.invite_slug,
                film_id=party.film_id,
            )
            sent += 1
        return sent
