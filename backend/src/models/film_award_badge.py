from __future__ import annotations

from enum import StrEnum

from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class FilmAwardBadgeKind(StrEnum):
    oscar_best_picture_nominee = 'oscar_best_picture_nominee'
    oscar_best_picture_winner = 'oscar_best_picture_winner'


class FilmAwardBadge(Base):
    """Oscar Best Picture nominee or winner badge attached to a film."""

    film_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('film.id', ondelete='CASCADE'),
        nullable=False,
    )
    kind: Mapped[str] = mapped_column(String(32), nullable=False)
    ceremony_year: Mapped[int] = mapped_column(Integer, nullable=False)

    __table_args__ = (
        UniqueConstraint(
            'film_id',
            'kind',
            'ceremony_year',
            name='uq_film_award_badge_film_kind_year',
        ),
        Index('ix_film_award_badge_film_id', 'film_id'),
    )
