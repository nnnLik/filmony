from __future__ import annotations

import datetime as dt
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, JSON, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class TasteQuizPairProgress(Base):
    """Accumulated knowledge edge guesser → owner."""

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    guesser_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    owner_user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    points_sum: Mapped[float] = mapped_column(Float, nullable=False, server_default='0')
    attempts: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0')
    played_card_ids: Mapped[list] = mapped_column(JSON, nullable=False, server_default='[]')
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint('guesser_user_id <> owner_user_id', name='ck_taste_quiz_no_self_pair'),
        CheckConstraint('attempts >= 0', name='ck_taste_quiz_attempts_nonneg'),
        CheckConstraint('points_sum >= 0', name='ck_taste_quiz_points_nonneg'),
        UniqueConstraint('guesser_user_id', 'owner_user_id', name='uq_taste_quiz_pair_progress'),
    )
