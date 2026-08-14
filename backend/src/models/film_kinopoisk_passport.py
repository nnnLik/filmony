from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base

if TYPE_CHECKING:
    from .film import Film


class FilmKinopoiskPassport(Base):
    """Kinopoisk passport metadata stored outside legacy ``film`` table ownership."""

    film_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('film.id', ondelete='CASCADE'),
        primary_key=True,
    )
    film_length: Mapped[int | None] = mapped_column(Integer, nullable=True)
    slogan: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating_kinopoisk: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating_imdb: Mapped[float | None] = mapped_column(Float, nullable=True)
    rating_age_limits: Mapped[str | None] = mapped_column(String(16), nullable=True)

    film: Mapped[Film] = relationship(back_populates='kinopoisk_passport')
