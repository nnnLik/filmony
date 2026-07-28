from __future__ import annotations

import datetime as dt
from uuid import UUID

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class WeeklyControversyState(Base):
    """Per-user weekly controversial title selection and digest idempotency."""

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    week_start: Mapped[dt.date] = mapped_column(Date(), nullable=False, index=True)
    anchor_film_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('film.id', ondelete='SET NULL'),
        nullable=True,
    )
    anchor_catalog_item_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('catalog_item.id', ondelete='SET NULL'),
        nullable=True,
    )
    title: Mapped[str | None] = mapped_column(String(255), nullable=True)
    spread: Mapped[float | None] = mapped_column(Float, nullable=True)
    rater_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_rating: Mapped[float | None] = mapped_column(Float, nullable=True)
    link_card_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('user_card.id', ondelete='SET NULL'),
        nullable=True,
    )
    sent_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
