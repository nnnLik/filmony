from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from daos.watch_party_dao import WatchPartyDAO
from models.watch_party_enums import WatchPartyMemberStatus, WatchPartyStatus
from services.watch_parties.ensure_active_watch_party import EnsureActiveWatchPartyService
from services.watch_parties.watch_party_broker import publish_watch_party_event

_AWAY_AFTER_SECONDS = 90
_LEFT_AFTER_AWAY_SECONDS = 30 * 60


@dataclass
class RecordWatchPartyHeartbeatService:
    """Refreshes member presence and sweeps away/left roster states."""

    _dao: WatchPartyDAO
    _ensure_active: EnsureActiveWatchPartyService
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
            _session=session,
        )

    async def execute(self, *, party_id: UUID, actor_user_id: UUID) -> None:
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

        changed = await self._sweep_presence(party_id=party.id, now=now)
        await self._session.commit()

        if changed:
            roster = await self._dao.list_member_rows(party.id)
            await publish_watch_party_event(
                party.id,
                event_type='presence',
                payload={
                    'members': [
                        {
                            'user_id': str(row.user_id),
                            'role': row.role,
                            'status': row.status,
                        }
                        for row in roster
                    ],
                },
            )

    async def _sweep_presence(self, *, party_id: UUID, now: dt.datetime) -> bool:
        rows = await self._dao.list_member_rows(party_id)
        changed = False
        for row in rows:
            if row.status == WatchPartyMemberStatus.left.value:
                continue
            last_seen = row.last_seen_at
            if last_seen.tzinfo is None:
                last_seen = last_seen.replace(tzinfo=dt.UTC)
            else:
                last_seen = last_seen.astimezone(dt.UTC)
            delta = (now - last_seen).total_seconds()
            if (
                delta >= _LEFT_AFTER_AWAY_SECONDS
                and row.status != WatchPartyMemberStatus.left.value
            ):
                await self._dao.update_member_status(
                    party_id=party_id,
                    user_id=row.user_id,
                    status=WatchPartyMemberStatus.left,
                )
                changed = True
            elif delta >= _AWAY_AFTER_SECONDS and row.status == WatchPartyMemberStatus.active.value:
                await self._dao.update_member_status(
                    party_id=party_id,
                    user_id=row.user_id,
                    status=WatchPartyMemberStatus.away,
                )
                changed = True
        return changed


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
        messages = await self._dao.list_messages(party_id=party.id, limit=50)
        return {
            'party_id': str(party.id),
            'status': party.status.value,
            'playback_state': party.playback_state,
            'members': [
                {
                    'user_id': str(row.user_id),
                    'display_name': row.display_name or 'Пользователь',
                    'photo_url': row.photo_url,
                    'role': row.role,
                    'status': row.status,
                    'joined_at': row.joined_at.isoformat(),
                }
                for row in members
            ],
            'messages': [
                {
                    'id': message.id,
                    'author_user_id': str(message.author_user_id),
                    'body': message.body,
                    'created_at': message.created_at.isoformat(),
                }
                for message in messages
            ],
        }
