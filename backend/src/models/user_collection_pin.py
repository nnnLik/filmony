from __future__ import annotations

import datetime as dt
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Index, Integer, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserCollectionPin(Base):
    """User-pinned collection shown on profile; ordered by sort_order."""

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
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0')
    pinned_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            'user_id',
            'collection_id',
            name='uq_user_collection_pin_user_collection',
        ),
        Index('ix_user_collection_pin_user_id_sort_order', 'user_id', 'sort_order'),
    )
