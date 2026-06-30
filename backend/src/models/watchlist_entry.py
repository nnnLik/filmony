from __future__ import annotations

import datetime as dt
from uuid import UUID

from sqlalchemy import JSON, DateTime, ForeignKey, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class WatchlistEntry(Base):
    """Provider-aware watchlist entry for a user."""

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    card_id: Mapped[str] = mapped_column(String(128), nullable=False, index=True)
    provider_meta: Mapped[dict] = mapped_column(JSON, nullable=False)
    watch_tag: Mapped[str] = mapped_column(String(32), nullable=False)
    watch_with_user_id: Mapped[UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('user.id', ondelete='SET NULL'),
        nullable=True,
    )
    watch_with_user_ids: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        server_default='[]',
    )
    created_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        Index('uq_watchlist_entry_user_card', 'user_id', 'card_id', unique=True),
        Index(
            'ix_watchlist_entry_user_id_created_at_id',
            'user_id',
            'created_at',
            'id',
            postgresql_ops={'created_at': 'DESC', 'id': 'DESC'},
        ),
    )
