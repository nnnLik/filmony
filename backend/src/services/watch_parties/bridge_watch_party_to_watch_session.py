from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from daos.watch_party_dao import WatchPartyDAO
from models.watch_party import WatchPartyWatchSessionLink
from models.watch_party_enums import WatchPartyMemberStatus, WatchPartyStatus
from services.films.get_film_by_id import GetFilmByIdService
from services.watch_parties.watch_party_redis import clear_party_redis, clear_user_watching
from services.watch_sessions.create_watch_session import CreateWatchSessionService


@dataclass(frozen=True, slots=True)
class BridgeWatchPartyResult:
    watch_session_id: UUID


@dataclass
class BridgeWatchPartyToWatchSessionService:
    """Ends a watch party and creates a planned co-rating watch session from its roster."""

    _dao: WatchPartyDAO
    _create_session: CreateWatchSessionService
    _film_service: GetFilmByIdService
    _session: AsyncSession

    class PartyNotFound(Exception):
        pass

    class PartyEnded(Exception):
        pass

    class HostRequired(Exception):
        pass

    class InvalidRoster(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        dao = WatchPartyDAO(session)
        return cls(
            _dao=dao,
            _create_session=CreateWatchSessionService.build(session),
            _film_service=GetFilmByIdService(session),
            _session=session,
        )

    async def execute(self, *, party_id: UUID, actor_user_id: UUID) -> BridgeWatchPartyResult:
        party = await self._dao.get_party_by_id(party_id)
        if party is None:
            raise self.PartyNotFound
        if party.status == WatchPartyStatus.ended:
            raise self.PartyEnded
        if party.host_user_id != actor_user_id:
            raise self.HostRequired

        member_rows = await self._dao.list_member_rows(party.id)
        active_members = [
            row
            for row in member_rows
            if row.status
            in (WatchPartyMemberStatus.active.value, WatchPartyMemberStatus.away.value)
        ]
        partner_ids = [row.user_id for row in active_members if row.user_id != actor_user_id]
        if not partner_ids:
            raise self.InvalidRoster

        if party.status == WatchPartyStatus.active:
            member_user_ids = [row.user_id for row in member_rows]
            await self._dao.update_party_status(
                party_id=party.id,
                status=WatchPartyStatus.ended,
                ended_at=dt.datetime.now(dt.UTC),
            )
            await clear_party_redis(party.id, member_user_ids)
            for user_id in member_user_ids:
                await clear_user_watching(user_id)

        film = await self._film_service.execute(party.film_id)
        if film is None:
            raise self.InvalidRoster

        watch_session = await self._create_session.execute(
            initiator_user_id=actor_user_id,
            partner_user_ids=partner_ids,
            anchor_film_id=party.film_id,
            anchor_catalog_item_id=None,
            source_watchlist_entry_id=None,
        )
        self._session.add(
            WatchPartyWatchSessionLink(
                watch_session_id=watch_session.id,
                watch_party_id=party.id,
            ),
        )
        await self._session.commit()
        return BridgeWatchPartyResult(watch_session_id=watch_session.id)
