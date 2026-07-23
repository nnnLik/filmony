from __future__ import annotations

import datetime as dt
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class TasteQuizSessionCard(Base):
    """Immutable snapshot of one card within a taste-quiz session."""

    id: Mapped[UUID] = mapped_column(Uuid(as_uuid=True), primary_key=True, default=uuid4)
    session_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('taste_quiz_session.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    card_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('user_card.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_title: Mapped[str] = mapped_column(String(255), nullable=False)
    snapshot_poster_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    snapshot_company: Mapped[str] = mapped_column(String(32), nullable=False)
    snapshot_mood_before: Mapped[str] = mapped_column(String(32), nullable=False)
    snapshot_owner_rating: Mapped[float] = mapped_column(Float, nullable=False)
    snapshot_mood_after: Mapped[str] = mapped_column(String(32), nullable=False)
    snapshot_watch_note: Mapped[str] = mapped_column(Text, nullable=False, server_default='')
    guess_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    points: Mapped[float | None] = mapped_column(Float, nullable=True)
    verdict_key: Mapped[str | None] = mapped_column(String(16), nullable=True)
    answered_at: Mapped[dt.datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
