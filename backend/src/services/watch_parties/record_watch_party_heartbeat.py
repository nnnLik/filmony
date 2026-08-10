from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from conf import settings
from daos.watch_party_dao import WatchPartyDAO
from models.watch_party_enums import WatchPartyMemberStatus
from services.films.get_film_by_id import GetFilmByIdService
from services.watch_parties.ensure_active_watch_party import EnsureActiveWatchPartyService
from services.watch_parties.watch_party_broker import publish_watch_party_event
from services.watch_parties.watch_party_member_positions import (
    build_member_payloads,
    persist_member_position,
)
from services.watch_parties.watch_party_redis import (
    clear_user_watching,
    list_chat_messages,
    set_user_watching,
)


def _away_after_seconds() -> float:
    interval = settings.watch_party.heartbeat_interval_seconds
    return float(interval * settings.watch_party.missed_heartbeats_away)


def _left_after_seconds() -> float:
    interval = settings.watch_party.heartbeat_interval_seconds
    return float(interval * settings.watch_party.missed_heartbeats_left)


def _watching_ttl_seconds() -> int:
    interval = settings.watch_party.heartbeat_interval_seconds
    left = settings.watch_party.missed_heartbeats_left
    return interval * left + interval


@dataclass
class RecordWatchPartyHeartbeatService:
    """Refreshes member presence and sweeps away/left roster states."""

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
        actor_user_id: UUID,
        position_ms: int | None = None,
        playing: bool | None = None,
    ) -> None:
        try:
            party = await self._ensure_active.execute(party_id)
        except EnsureActiveWatchPartyService.PartyNotFound:
            raise self.PartyNotFound from None
        except EnsureActiveWatchPartyService.PartyEnded:
            raise self.PartyEnded from None

        member = await self._dao.get_member(party_id=party.id, user_id=actor_user_id)
        if member is None or member.status == WatchPartyMemberStatus.left:
            raise self.NotMember

        now = dt.datetime.now(dt.UTC)
        await self._dao.update_member_status(
            party_id=party.id,
            user_id=actor_user_id,
            status=WatchPartyMemberStatus.active,
            last_seen_at=now,
        )

        film = await self._film_service.execute(party.film_id)
        film_title = film.title if film is not None else ''
        await set_user_watching(
            actor_user_id,
            {
                'film_id': party.film_id,
                'film_title': film_title,
                'party_id': str(party.id),
            },
            ttl_seconds=_watching_ttl_seconds(),
        )

        position_payload: dict[str, object] | None = None
        if member.role.value == 'host':
            playback = party.playback_state or {}
            position_payload = await persist_member_position(
                party_id=party.id,
                user_id=actor_user_id,
                position_ms=int(playback.get('position_ms', 0)),
                playing=bool(playback.get('playing', False)),
            )
        elif position_ms is not None:
            position_payload = await persist_member_position(
                party_id=party.id,
                user_id=actor_user_id,
                position_ms=position_ms,
                playing=bool(playing),
            )

        changed, left_user_ids = await self._sweep_presence(party_id=party.id, now=now)
        await self._session.commit()

        for user_id in left_user_ids:
            await clear_user_watching(user_id)

        if position_payload is not None:
            await publish_watch_party_event(
                party.id,
                event_type='member_position',
                payload=position_payload,
            )

        if changed:
            roster = await self._dao.list_member_rows(party.id)
            await publish_watch_party_event(
                party.id,
                event_type='presence',
                payload={
                    'members': await build_member_payloads(party=party, member_rows=roster),
                },
            )

    async def _sweep_presence(
        self,
        *,
        party_id: UUID,
        now: dt.datetime,
    ) -> tuple[bool, list[UUID]]:
        rows = await self._dao.list_member_rows(party_id)
        changed = False
        left_user_ids: list[UUID] = []
        away_after = _away_after_seconds()
        left_after = _left_after_seconds()
        for row in rows:
            if row.status == WatchPartyMemberStatus.left.value:
                continue
            last_seen = row.last_seen_at
            if last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=dt.UTC)
            else:
                last_seen = last_seen.astimezone(dt.UTC)
            delta = (now - last_seen).total_seconds()
            if delta >= left_after and row.status != WatchPartyMemberStatus.left.value:
                await self._dao.update_member_status(
                    party_id=party_id,
                    user_id=row.user_id,
                    status=WatchPartyMemberStatus.left,
                )
                changed = True
                left_user_ids.append(row.user_id)
            elif delta >= away_after and row.status == WatchPartyMemberStatus.active.value:
                await self._dao.update_member_status(
                    party_id=party_id,
                    user_id=row.user_id,
                    status=WatchPartyMemberStatus.away,
                )
                changed = True
        return changed, left_user_ids


@dataclass
class BuildWatchPartySnapshotPayloadService:
    """Builds SSE snapshot payload for a party."""

    _dao: WatchPartyDAO
    _ensure_active: EnsureActiveWatchPartyService

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        dao = WatchPartyDAO(session)
        return cls(
            _dao=dao,
            _ensure_active=EnsureActiveWatchPartyService.build(dao),
        )

    async def execute(self, *, party_id: UUID) -> dict:
        party = await self._ensure_active.execute(party_id)
        members = await self._dao.list_member_rows(party.id)
        messages = await list_chat_messages(
            party.id,
            before_id=None,
            limit=settings.watch_party.chat_page_size,
        )
        member_payloads = await build_member_payloads(party=party, member_rows=members)
        return {
            'party_id': str(party.id),
            'status': party.status.value,
            'playback_state': party.playback_state,
            'members': member_payloads,
            'messages': [
                {
                    'id': int(message['id']),
                    'author_user_id': str(message['author_user_id']),
                    'body': str(message['body']),
                    'created_at': str(message['created_at']),
                }
                for message in messages
            ],
        }
