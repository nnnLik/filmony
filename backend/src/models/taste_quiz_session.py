from __future__ import annotations

import datetime as dt
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Uuid, func
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base
from .taste_quiz_enums import TasteQuizSessionStatus


class TasteQuizSession(Base):
    """One taste-quiz round (up to 10 cards) for a guesser–owner pair."""

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
    status: Mapped[TasteQuizSessionStatus] = mapped_column(
        SAEnum(TasteQuizSessionStatus, native_enum=False, length=16),
        nullable=False,
        server_default=TasteQuizSessionStatus.ACTIVE.value,
        index=True,
    )
    round_points: Mapped[float] = mapped_column(Float, nullable=False, server_default='0')
    started_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    finished_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
