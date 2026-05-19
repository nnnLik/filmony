from __future__ import annotations

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CardTag(Base):
    """Free-form tag on a user card; persists in legacy `movie_card_tag` table."""

    __tablename__ = 'movie_card_tag'

    card_id: Mapped[int] = mapped_column(
        'movie_card_id',
        ForeignKey('movie_card.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    tag: Mapped[str] = mapped_column(String(40), nullable=False)

    __table_args__ = (UniqueConstraint('movie_card_id', 'tag', name='uq_movie_card_tag_unique'),)
