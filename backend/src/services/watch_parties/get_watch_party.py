from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from daos.watch_party_dao import WatchPartyDAO
from services.films.get_film_by_id import GetFilmByIdService
from services.watch_parties.ensure_active_watch_party import EnsureActiveWatchPartyService
from services.watch_parties.helpers import build_invite_url
from services.watch_parties.watch_party_member_positions import build_member_payloads


@dataclass(frozen=True, slots=True)
class WatchPartyMemberDTO:
    user_id: UUID
    display_name: str
    photo_url: str | None
    role: str
    status: str
    joined_at: str
    position_ms: int | None
    position_playing: bool | None
    position_at: str | None


@dataclass(frozen=True, slots=True)
class WatchPartySnapshotDTO:
    id: UUID
    invite_slug: str
    invite_url: str
    status: str
    film_id: int
    film_title: str
    film_poster_url: str | None
    playback_iframe_url: str
    playback_expires_at: str
    playback_state: dict
    host_user_id: UUID
    members: list[WatchPartyMemberDTO]
    viewer_role: str | None
    viewer_status: str | None


@dataclass
class GetWatchPartyService:
    """Returns a watch party snapshot for members and landing pages."""

    _dao: WatchPartyDAO
    _ensure_active: EnsureActiveWatchPartyService
    _film_service: GetFilmByIdService
    _session: AsyncSession

    class PartyNotFound(Exception):
        pass

    class PartyEnded(Exception):
        pass

    class NotMember(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        dao = WatchPartyDAO(session)
        return cls(
            _dao=dao,
            _ensure_active=EnsureActiveWatchPartyService.build(dao),
            _film_service=GetFilmByIdService(session),
            _session=session,
        )

    async def execute(
        self,
        *,
        party_id: UUID,
        viewer_user_id: UUID,
        require_membership: bool = True,
    ) -> WatchPartySnapshotDTO:
        try:
            party = await self._ensure_active.execute(party_id)
        except EnsureActiveWatchPartyService.PartyNotFound:
            raise self.PartyNotFound from None
        except EnsureActiveWatchPartyService.PartyEnded:
            raise self.PartyEnded from None

        member = await self._dao.get_member(party_id=party.id, user_id=viewer_user_id)
        if require_membership and member is None:
            raise self.NotMember
        if member is not None and member.status.value == 'left':
            raise self.NotMember

        film = await self._film_service.execute(party.film_id)
        film_title = film.title if film is not None else ''
        film_poster = film.poster_url if film is not None else None

        member_rows = await self._dao.list_member_rows(party.id)
        member_payloads = await build_member_payloads(party=party, member_rows=member_rows)
        members = [
            WatchPartyMemberDTO(
                user_id=UUID(payload['user_id']),
                display_name=str(payload['display_name']),
                photo_url=payload['photo_url'],
                role=str(payload['role']),
                status=str(payload['status']),
                joined_at=str(payload['joined_at']),
                position_ms=payload['position_ms'],
                position_playing=payload['position_playing'],
                position_at=payload['position_at'],
            )
            for payload in member_payloads
        ]

        return WatchPartySnapshotDTO(
            id=party.id,
            invite_slug=party.invite_slug,
            invite_url=build_invite_url(party.invite_slug),
            status=party.status.value,
            film_id=party.film_id,
            film_title=film_title,
            film_poster_url=film_poster,
            playback_iframe_url=party.playback_iframe_url,
            playback_expires_at=party.playback_expires_at.isoformat(),
            playback_state=party.playback_state,
            host_user_id=party.host_user_id,
            members=members,
            viewer_role=member.role.value if member is not None else None,
            viewer_status=member.status.value if member is not None else None,
        )
