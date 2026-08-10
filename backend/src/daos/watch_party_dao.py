from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from models.watch_party import WatchParty, WatchPartyMember, WatchPartyMessage
from models.watch_party_enums import WatchPartyMemberStatus, WatchPartyStatus


@dataclass(frozen=True, slots=True)
class WatchPartyMemberRow:
    party_id: UUID
    user_id: UUID
    role: str
    status: str
    last_seen_at: dt.datetime
    joined_at: dt.datetime
    display_name: str | None
    photo_url: str | None


class WatchPartyDAO:
    """Persistence gateway for live watch party rooms."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_party_by_id(self, party_id: UUID) -> WatchParty | None:
        return await self._session.get(WatchParty, party_id)

    async def get_party_by_slug(self, invite_slug: str) -> WatchParty | None:
        result = await self._session.execute(
            select(WatchParty).where(WatchParty.invite_slug == invite_slug),
        )
        return result.scalar_one_or_none()

    async def insert_party(self, party: WatchParty) -> WatchParty:
        self._session.add(party)
        await self._session.flush()
        return party

    async def insert_member(self, member: WatchPartyMember) -> WatchPartyMember:
        self._session.add(member)
        await self._session.flush()
        return member

    async def get_member(self, *, party_id: UUID, user_id: UUID) -> WatchPartyMember | None:
        result = await self._session.execute(
            select(WatchPartyMember).where(
                WatchPartyMember.party_id == party_id,
                WatchPartyMember.user_id == user_id,
            ),
        )
        return result.scalar_one_or_none()

    async def count_roster_members(self, party_id: UUID) -> int:
        result = await self._session.execute(
            select(func.count())
            .select_from(WatchPartyMember)
            .where(
                WatchPartyMember.party_id == party_id,
                WatchPartyMember.status.in_(
                    (
                        WatchPartyMemberStatus.active.value,
                        WatchPartyMemberStatus.away.value,
                    ),
                ),
            ),
        )
        return int(result.scalar_one())

    async def find_active_membership_for_user(
        self,
        user_id: UUID,
        *,
        exclude_party_id: UUID | None = None,
    ) -> tuple[WatchParty, WatchPartyMember] | None:
        stmt = (
            select(WatchParty, WatchPartyMember)
            .join(WatchPartyMember, WatchPartyMember.party_id == WatchParty.id)
            .where(
                WatchPartyMember.user_id == user_id,
                WatchPartyMember.status.in_(
                    (
                        WatchPartyMemberStatus.active.value,
                        WatchPartyMemberStatus.away.value,
                    ),
                ),
                WatchParty.status == WatchPartyStatus.active.value,
            )
        )
        if exclude_party_id is not None:
            stmt = stmt.where(WatchParty.id != exclude_party_id)
        result = await self._session.execute(stmt.limit(1))
        row = result.first()
        if row is None:
            return None
        party, member = row
        return party, member

    async def list_member_rows(self, party_id: UUID) -> list[WatchPartyMemberRow]:
        result = await self._session.execute(
            select(WatchPartyMember, User)
            .join(User, User.id == WatchPartyMember.user_id)
            .where(WatchPartyMember.party_id == party_id)
            .order_by(WatchPartyMember.joined_at.asc()),
        )
        rows: list[WatchPartyMemberRow] = []
        for member, user in result.all():
            rows.append(
                WatchPartyMemberRow(
                    party_id=member.party_id,
                    user_id=member.user_id,
                    role=member.role.value,
                    status=member.status.value,
                    last_seen_at=member.last_seen_at,
                    joined_at=member.joined_at,
                    display_name=user.display_name,
                    photo_url=user.photo_url,
                ),
            )
        return rows

    async def update_member_status(
        self,
        *,
        party_id: UUID,
        user_id: UUID,
        status: WatchPartyMemberStatus,
        last_seen_at: dt.datetime | None = None,
    ) -> None:
        values: dict = {'status': status.value}
        if last_seen_at is not None:
            values['last_seen_at'] = last_seen_at
        await self._session.execute(
            update(WatchPartyMember)
            .where(
                WatchPartyMember.party_id == party_id,
                WatchPartyMember.user_id == user_id,
            )
            .values(**values),
        )

    async def update_party_playback(
        self,
        *,
        party_id: UUID,
        iframe_url: str,
        expires_at: dt.datetime,
    ) -> None:
        await self._session.execute(
            update(WatchParty)
            .where(WatchParty.id == party_id)
            .values(
                playback_iframe_url=iframe_url,
                playback_expires_at=expires_at,
            ),
        )

    async def update_party_status(
        self,
        *,
        party_id: UUID,
        status: WatchPartyStatus,
        ended_at: dt.datetime | None = None,
    ) -> None:
        values: dict = {'status': status.value}
        if ended_at is not None:
            values['ended_at'] = ended_at
        await self._session.execute(
            update(WatchParty).where(WatchParty.id == party_id).values(**values),
        )

    async def update_playback_state(self, *, party_id: UUID, playback_state: dict) -> None:
        await self._session.execute(
            update(WatchParty)
            .where(WatchParty.id == party_id)
            .values(playback_state=playback_state),
        )

    async def list_messages(
        self,
        *,
        party_id: UUID,
        limit: int,
        before_id: int | None = None,
    ) -> list[WatchPartyMessage]:
        stmt = select(WatchPartyMessage).where(WatchPartyMessage.party_id == party_id)
        if before_id is not None:
            stmt = stmt.where(WatchPartyMessage.id < before_id)
        stmt = stmt.order_by(WatchPartyMessage.id.desc()).limit(limit)
        result = await self._session.execute(stmt)
        messages = list(result.scalars().all())
        messages.reverse()
        return messages

    async def insert_message(self, message: WatchPartyMessage) -> WatchPartyMessage:
        self._session.add(message)
        await self._session.flush()
        return message

    async def get_message(self, message_id: int) -> WatchPartyMessage | None:
        return await self._session.get(WatchPartyMessage, message_id)

    async def delete_message(self, message_id: int) -> None:
        message = await self.get_message(message_id)
        if message is not None:
            await self._session.delete(message)
