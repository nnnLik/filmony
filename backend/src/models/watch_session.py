from __future__ import annotations

import datetime as dt
from uuid import UUID, uuid4

from sqlalchemy import JSON, DateTime, ForeignKey, Index, Integer, Uuid, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .watch_session_enums import WatchSessionStatus


class WatchSession(Base):
    """Co-view session started from a watch-with watchlist invite."""

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    initiator_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    anchor_film_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('film.id', ondelete='CASCADE'),
        nullable=True,
        index=True,
    )
    anchor_catalog_item_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('catalog_item.id', ondelete='CASCADE'),
        nullable=True,
        index=True,
    )
    participant_user_ids: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        server_default='[]',
    )
    status: Mapped[WatchSessionStatus] = mapped_column(
        SAEnum(WatchSessionStatus, native_enum=False, length=16),
        nullable=False,
        server_default=WatchSessionStatus.planned.value,
        index=True,
    )
    source_watchlist_entry_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('watchlist_entry.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    source_watch_party_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('watch_party.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    first_rated_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    nudge_sent_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    feed_post_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey(
            'feed_post.id',
            ondelete='SET NULL',
            name='fk_watch_session_feed_post_id',
            use_alter=True,
        ),
        nullable=True,
        index=True,
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index(
            'ix_watch_session_status_first_rated_at',
            'status',
            'first_rated_at',
        ),
    )
