from __future__ import annotations

import datetime as dt
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, Integer, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserAchievement(Base):
    """Sticky unlock when a user completes a curated collection."""

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    achievement_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('achievement.id', ondelete='CASCADE'),
        nullable=False,
    )
    unlocked_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint(
            'user_id',
            'achievement_id',
            name='uq_user_achievement_user_achievement',
        ),
    )
