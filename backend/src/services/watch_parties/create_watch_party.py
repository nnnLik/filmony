from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from conf import settings
from daos.watch_party_dao import WatchPartyDAO
from models.watch_party import WatchParty, WatchPartyMember
from models.watch_party_enums import WatchPartyMemberRole, WatchPartyMemberStatus, WatchPartyStatus
from services.films.resolve_film_playback import ResolveFilmPlaybackService
from services.watch_parties.ensure_active_watch_party import EnsureActiveWatchPartyService
from services.watch_parties.helpers import (
    build_initial_playback_state,
    build_invite_url,
    generate_invite_slug,
)


@dataclass(frozen=True, slots=True)
class CreateWatchPartyResult:
    party_id: UUID
    invite_slug: str
    invite_url: str


@dataclass
class CreateWatchPartyService:
    """Creates a live watch party after verifying playback is available."""

    _dao: WatchPartyDAO
    _ensure_active: EnsureActiveWatchPartyService
    _playback_service: ResolveFilmPlaybackService
    _session: AsyncSession

    class AlreadyInActiveParty(Exception):
        def __init__(self, *, active_party_id: UUID, invite_slug: str) -> None:
            self.active_party_id = active_party_id
            self.invite_slug = invite_slug
            super().__init__()

    class PlaybackUnavailable(Exception):
        pass

    class FilmNotFound(Exception):
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

    async def execute(self, *, actor_user_id: UUID, film_id: int) -> CreateWatchPartyResult:
        existing = await self._dao.find_active_membership_for_user(actor_user_id)
        if existing is not None:
            party, _member = existing
            try:
                await self._ensure_active.execute(party.id)
            except EnsureActiveWatchPartyService.PartyEnded:
                pass
            except EnsureActiveWatchPartyService.PartyNotFound:
                pass
            else:
                raise self.AlreadyInActiveParty(
                    active_party_id=party.id,
                    invite_slug=party.invite_slug,
                )

        try:
            playback = await self._playback_service.execute(film_id, actor_user_id)
        except ResolveFilmPlaybackService.FilmNotFound:
            raise self.FilmNotFound from None
        except ResolveFilmPlaybackService.PlaybackUnavailable:
            raise self.PlaybackUnavailable from None

        invite_slug = generate_invite_slug()
        party = WatchParty(
            invite_slug=invite_slug,
            host_user_id=actor_user_id,
            film_id=film_id,
            playback_iframe_url=playback.iframe_url,
            playback_expires_at=playback.expires_at,
            status=WatchPartyStatus.active,
            max_members=None,
            playback_state=build_initial_playback_state(host_user_id=actor_user_id),
        )
        await self._dao.insert_party(party)

        member = WatchPartyMember(
            party_id=party.id,
            user_id=actor_user_id,
            role=WatchPartyMemberRole.host,
            status=WatchPartyMemberStatus.active,
        )
        await self._dao.insert_member(member)
        await self._session.commit()

        _ = settings.watch_party.max_active_per_user  # enforced above
        return CreateWatchPartyResult(
            party_id=party.id,
            invite_slug=party.invite_slug,
            invite_url=build_invite_url(party.invite_slug),
        )
