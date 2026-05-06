from __future__ import annotations

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class MovieCardTag(Base):
    movie_card_id: Mapped[int] = mapped_column(
        ForeignKey('movie_card.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    tag: Mapped[str] = mapped_column(String(40), nullable=False)

    __table_args__ = (UniqueConstraint('movie_card_id', 'tag', name='uq_movie_card_tag_unique'),)
