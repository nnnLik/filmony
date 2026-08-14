from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from conf import settings
from daos.watch_party_dao import WatchPartyDAO
from models.watch_party import WatchPartyMember
from models.watch_party_enums import WatchPartyMemberRole, WatchPartyMemberStatus
from services.films.resolve_film_playback import ResolveFilmPlaybackService
from services.watch_parties.ensure_active_watch_party import EnsureActiveWatchPartyService


@dataclass
class JoinWatchPartyService:
    """Adds an authenticated user to a watch party roster."""

    _dao: WatchPartyDAO
    _ensure_active: EnsureActiveWatchPartyService
    _playback_service: ResolveFilmPlaybackService
    _session: AsyncSession

    class PartyNotFound(Exception):
        pass

    class PartyEnded(Exception):
        pass

    class AlreadyInActiveParty(Exception):
        def __init__(self, *, active_party_id: UUID, invite_slug: str) -> None:
            self.active_party_id = active_party_id
            self.invite_slug = invite_slug
            super().__init__()

    class PartyFull(Exception):
        pass

    class PlaybackUnavailable(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        dao = WatchPartyDAO(session)
        return cls(
            _dao=dao,
            _ensure_active=EnsureActiveWatchPartyService.build(dao),
            _playback_service=ResolveFilmPlaybackService.build(session),
            _session=session,
        )

    async def execute(self, *, party_id: UUID, actor_user_id: UUID) -> None:
        try:
            party = await self._ensure_active.execute(party_id)
        except EnsureActiveWatchPartyService.PartyNotFound:
            raise self.PartyNotFound from None
        except EnsureActiveWatchPartyService.PartyEnded:
            raise self.PartyEnded from None

        existing_elsewhere = await self._dao.find_active_membership_for_user(
            actor_user_id,
            exclude_party_id=party.id,
        )
        if existing_elsewhere is not None:
            other_party, _member = existing_elsewhere
            try:
                await self._ensure_active.execute(other_party.id)
            except EnsureActiveWatchPartyService.PartyEnded:
                pass
            except EnsureActiveWatchPartyService.PartyNotFound:
                pass
            else:
                raise self.AlreadyInActiveParty(
                    active_party_id=other_party.id,
                    invite_slug=other_party.invite_slug,
                )

        member = await self._dao.get_member(party_id=party.id, user_id=actor_user_id)
        if member is None:
            roster_count = await self._dao.count_roster_members(party.id)
            hard_max = settings.watch_party.hard_max_members
            if roster_count >= hard_max:
                raise self.PartyFull

        now = dt.datetime.now(dt.UTC)
        if party.playback_expires_at <= now:
            try:
                playback = await self._playback_service.execute(party.film_id, actor_user_id)
            except ResolveFilmPlaybackService.PlaybackUnavailable:
                raise self.PlaybackUnavailable from None
            await self._dao.update_party_playback(
                party_id=party.id,
                iframe_url=playback.iframe_url,
                expires_at=playback.expires_at,
            )

        if member is None:
            new_member = WatchPartyMember(
                party_id=party.id,
                user_id=actor_user_id,
                role=WatchPartyMemberRole.guest,
                status=WatchPartyMemberStatus.active,
                last_seen_at=now,
            )
            await self._dao.insert_member(new_member)
        else:
            await self._dao.update_member_status(
                party_id=party.id,
                user_id=actor_user_id,
                status=WatchPartyMemberStatus.active,
                last_seen_at=now,
            )

        await self._session.commit()
