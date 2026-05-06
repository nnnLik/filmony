from __future__ import annotations

import datetime as dt
from uuid import UUID

from sqlalchemy import DateTime, Float, ForeignKey, String, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class MovieCard(Base):
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    film_id: Mapped[int] = mapped_column(
        ForeignKey('film.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    company: Mapped[str] = mapped_column(String(32), nullable=False)
    mood_before: Mapped[str] = mapped_column(String(32), nullable=False)
    mood_after: Mapped[str] = mapped_column(String(32), nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (UniqueConstraint('user_id', 'film_id', name='uq_movie_card_user_film'),)
