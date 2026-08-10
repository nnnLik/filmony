from __future__ import annotations

import datetime as dt
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy import Enum as SAEnum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .watch_party_enums import WatchPartyMemberRole, WatchPartyMemberStatus, WatchPartyStatus


class WatchParty(Base):
    """Live co-view room: chat, presence, and host playback state."""

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    invite_slug: Mapped[str] = mapped_column(String(32), unique=True, nullable=False, index=True)
    host_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    film_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('film.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    playback_iframe_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    playback_expires_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[WatchPartyStatus] = mapped_column(
        SAEnum(WatchPartyStatus, native_enum=False, length=16),
        nullable=False,
        server_default=WatchPartyStatus.active.value,
        index=True,
    )
    max_members: Mapped[int | None] = mapped_column(Integer, nullable=True)
    playback_state: Mapped[dict] = mapped_column(JSONB, nullable=False)
    ended_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class WatchPartyMember(Base):
    """Roster entry for a live watch party."""

    party_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('watch_party.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    role: Mapped[WatchPartyMemberRole] = mapped_column(
        SAEnum(WatchPartyMemberRole, native_enum=False, length=8),
        nullable=False,
    )
    status: Mapped[WatchPartyMemberStatus] = mapped_column(
        SAEnum(WatchPartyMemberStatus, native_enum=False, length=8),
        nullable=False,
        server_default=WatchPartyMemberStatus.active.value,
        index=True,
    )
    last_seen_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    joined_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint('party_id', 'user_id', name='uq_watch_party_member_party_user'),
        Index('ix_watch_party_member_party_status', 'party_id', 'status'),
        Index('ix_watch_party_member_user_status', 'user_id', 'status'),
    )
