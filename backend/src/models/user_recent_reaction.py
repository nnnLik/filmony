from __future__ import annotations

import datetime as dt
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserRecentReaction(Base):
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    reaction_type_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('reaction_type.id', ondelete='RESTRICT'),
        nullable=False,
    )
    last_used_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            'user_id',
            'reaction_type_id',
            name='uq_user_recent_reaction_user_rt',
        ),
    )
