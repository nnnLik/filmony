from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, Integer, SmallInteger, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base

MAX_ACHIEVEMENT_PINS = 3


class UserAchievementPin(Base):
    """User showcase slot for an unlocked achievement on public profile."""

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
    slot_index: Mapped[int] = mapped_column(SmallInteger, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            'user_id',
            'slot_index',
            name='uq_user_achievement_pin_user_slot',
        ),
        UniqueConstraint(
            'user_id',
            'achievement_id',
            name='uq_user_achievement_pin_user_achievement',
        ),
    )
