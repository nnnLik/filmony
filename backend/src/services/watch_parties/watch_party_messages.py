from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from conf import settings
from daos.watch_party_dao import WatchPartyDAO
from models.watch_party import WatchPartyMessage
from models.watch_party_enums import WatchPartyMemberStatus
from services.watch_parties.ensure_active_watch_party import EnsureActiveWatchPartyService
from services.watch_parties.watch_party_broker import publish_watch_party_event

_MAX_BODY_LEN = 500
_MAX_MESSAGES_PER_MINUTE = 20


@dataclass(frozen=True, slots=True)
class WatchPartyMessageDTO:
    id: int
    party_id: UUID
    author_user_id: UUID
    body: str
    created_at: str


@dataclass
class CreateWatchPartyMessageService:
    """Persists a chat message and broadcasts it to room subscribers."""

    _dao: WatchPartyDAO
    _ensure_active: EnsureActiveWatchPartyService
    _session: AsyncSession
    _message_timestamps: dict[tuple[UUID, UUID], list[dt.datetime]]

    class PartyNotFound(Exception):
        pass

    class PartyEnded(Exception):
        pass

    class NotMember(Exception):
        pass

    class BodyTooLong(Exception):
        pass

    class RateLimited(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        dao = WatchPartyDAO(session)
        return cls(
            _dao=dao,
            _ensure_active=EnsureActiveWatchPartyService.build(dao),
            _session=session,
            _message_timestamps={},
        )

    async def execute(
        self,
        *,
        party_id: UUID,
        actor_user_id: UUID,
        body: str,
    ) -> WatchPartyMessageDTO:
        try:
            party = await self._ensure_active.execute(party_id)
        except EnsureActiveWatchPartyService.PartyNotFound:
            raise self.PartyNotFound from None
        except EnsureActiveWatchPartyService.PartyEnded:
            raise self.PartyEnded from None

        member = await self._dao.get_member(party_id=party.id, user_id=actor_user_id)
        if member is None or member.status == WatchPartyMemberStatus.left:
            raise self.NotMember

        trimmed = body.strip()
        if not trimmed:
            raise self.BodyTooLong
        if len(trimmed) > _MAX_BODY_LEN:
            raise self.BodyTooLong

        now = dt.datetime.now(dt.UTC)
        self._enforce_rate_limit(party_id=party.id, actor_user_id=actor_user_id, now=now)

        message = WatchPartyMessage(
            party_id=party.id,
            author_user_id=actor_user_id,
            body=trimmed,
        )
        saved = await self._dao.insert_message(message)
        await self._session.commit()

        dto = WatchPartyMessageDTO(
            id=saved.id,
            party_id=saved.party_id,
            author_user_id=saved.author_user_id,
            body=saved.body,
            created_at=saved.created_at.isoformat(),
        )
        await publish_watch_party_event(
            party.id,
            event_type='chat_message',
            payload={
                'message': {
                    'id': dto.id,
                    'author_user_id': str(dto.author_user_id),
                    'body': dto.body,
                    'created_at': dto.created_at,
                },
            },
        )
        return dto

    def _enforce_rate_limit(
        self,
        *,
        party_id: UUID,
        actor_user_id: UUID,
        now: dt.datetime,
    ) -> None:
        key = (party_id, actor_user_id)
        window_start = now - dt.timedelta(minutes=1)
        recent = [ts for ts in self._message_timestamps.get(key, []) if ts >= window_start]
        if len(recent) >= _MAX_MESSAGES_PER_MINUTE:
            raise self.RateLimited
        recent.append(now)
        self._message_timestamps[key] = recent


@dataclass
class ListWatchPartyMessagesService:
    """Returns paginated chat history for a party member."""

    _dao: WatchPartyDAO
    _ensure_active: EnsureActiveWatchPartyService

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
        )

    async def execute(
        self,
        *,
        party_id: UUID,
        actor_user_id: UUID,
        cursor: int | None = None,
        limit: int = 50,
    ) -> list[WatchPartyMessageDTO]:
        try:
            party = await self._ensure_active.execute(party_id)
        except EnsureActiveWatchPartyService.PartyNotFound:
            raise self.PartyNotFound from None
        except EnsureActiveWatchPartyService.PartyEnded:
            raise self.PartyEnded from None

        member = await self._dao.get_member(party_id=party.id, user_id=actor_user_id)
        if member is None or member.status == WatchPartyMemberStatus.left:
            raise self.NotMember

        capped = min(max(limit, 1), 50)
        messages = await self._dao.list_messages(
            party_id=party.id,
            limit=capped,
            before_id=cursor,
        )
        return [
            WatchPartyMessageDTO(
                id=message.id,
                party_id=message.party_id,
                author_user_id=message.author_user_id,
                body=message.body,
                created_at=message.created_at.isoformat(),
            )
            for message in messages
        ]


@dataclass
class DeleteWatchPartyMessageService:
    """Deletes the author's message within the allowed window."""

    _dao: WatchPartyDAO
    _ensure_active: EnsureActiveWatchPartyService
    _session: AsyncSession

    class PartyNotFound(Exception):
        pass

    class PartyEnded(Exception):
        pass

    class NotMember(Exception):
        pass

    class MessageNotFound(Exception):
        pass

    class Forbidden(Exception):
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
        message_id: int,
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

        message = await self._dao.get_message(message_id)
        if message is None or message.party_id != party.id:
            raise self.MessageNotFound
        if message.author_user_id != actor_user_id:
            raise self.Forbidden

        created_at = message.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=dt.UTC)
        if dt.datetime.now(dt.UTC) - created_at.astimezone(dt.UTC) > dt.timedelta(minutes=2):
            raise self.Forbidden

        await self._dao.delete_message(message_id)
        await self._session.commit()

        await publish_watch_party_event(
            party.id,
            event_type='chat_message_deleted',
            payload={'message_id': message_id},
        )
