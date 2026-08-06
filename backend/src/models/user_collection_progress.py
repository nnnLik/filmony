from __future__ import annotations

import datetime as dt
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserCollectionProgress(Base):
    """Per-user rated/total progress against a collection."""

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    collection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('collection.id', ondelete='CASCADE'),
        nullable=False,
    )
    rated_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0')
    total_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0')
    completed_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint(
            'user_id',
            'collection_id',
            name='uq_user_collection_progress_user_collection',
        ),
    )
