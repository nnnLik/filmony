from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Person(Base):
    """Kinopoisk person (v1: actors from film cast)."""

    kinopoisk_id: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    poster_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    updated_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=dt.datetime.now(dt.UTC),
    )

    __table_args__ = (UniqueConstraint('kinopoisk_id', name='uq_person_kinopoisk_id'),)
