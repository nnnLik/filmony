from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from conf import settings
from daos.watch_party_dao import WatchPartyDAO
from models.watch_party_enums import WatchPartyMemberStatus
from services.watch_parties.ensure_active_watch_party import EnsureActiveWatchPartyService
from services.watch_parties.watch_party_broker import publish_watch_party_event
from services.watch_parties.watch_party_redis import (
    append_chat_message,
    delete_chat_message,
    enforce_message_rate_limit,
    list_chat_messages,
)

_MAX_BODY_LEN = 500


@dataclass(frozen=True, slots=True)
class WatchPartyMessageDTO:
    id: int
    party_id: UUID
    author_user_id: UUID
    body: str
    created_at: str


@dataclass
class CreateWatchPartyMessageService:
    """Stores a chat message in Redis and broadcasts it to room subscribers."""

    _dao: WatchPartyDAO
    _ensure_active: EnsureActiveWatchPartyService

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
    def build(cls, session) -> Self:
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

        allowed = await enforce_message_rate_limit(
            party.id,
            actor_user_id,
            limit=20,
            window_seconds=60,
        )
        if not allowed:
            raise self.RateLimited

        now_iso = dt.datetime.now(dt.UTC).isoformat()
        saved = await append_chat_message(
            party.id,
            author_user_id=actor_user_id,
            body=trimmed,
            created_at=now_iso,
        )

        dto = WatchPartyMessageDTO(
            id=int(saved['id']),
            party_id=party.id,
            author_user_id=actor_user_id,
            body=str(saved['body']),
            created_at=str(saved['created_at']),
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


@dataclass
class ListWatchPartyMessagesService:
    """Returns paginated chat history for a party member from Redis."""

    _dao: WatchPartyDAO
    _ensure_active: EnsureActiveWatchPartyService

    class PartyNotFound(Exception):
        pass

    class PartyEnded(Exception):
        pass

    class NotMember(Exception):
        pass

    @classmethod
    def build(cls, session) -> Self:
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

        capped = min(max(limit, 1), settings.watch_party.chat_page_size)
        messages = await list_chat_messages(
            party.id,
            before_id=cursor,
            limit=capped,
        )
        return [
            WatchPartyMessageDTO(
                id=int(message['id']),
                party_id=party.id,
                author_user_id=UUID(str(message['author_user_id'])),
                body=str(message['body']),
                created_at=str(message['created_at']),
            )
            for message in messages
        ]


@dataclass
class DeleteWatchPartyMessageService:
    """Deletes the author's message from ephemeral Redis chat."""

    _dao: WatchPartyDAO
    _ensure_active: EnsureActiveWatchPartyService

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
    def build(cls, session) -> Self:
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

        messages = await list_chat_messages(
            party.id, before_id=None, limit=settings.watch_party.chat_max_messages
        )
        target = next((m for m in messages if int(m['id']) == message_id), None)
        if target is None:
            raise self.MessageNotFound
        if UUID(str(target['author_user_id'])) != actor_user_id:
            raise self.Forbidden

        created_at = dt.datetime.fromisoformat(str(target['created_at']))
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=dt.UTC)
        if dt.datetime.now(dt.UTC) - created_at.astimezone(dt.UTC) > dt.timedelta(minutes=2):
            raise self.Forbidden

        removed = await delete_chat_message(party.id, message_id)
        if not removed:
            raise self.MessageNotFound

        await publish_watch_party_event(
            party.id,
            event_type='chat_message_deleted',
            payload={'message_id': message_id},
        )
