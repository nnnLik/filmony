from __future__ import annotations

from sqlalchemy import ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CollectionFilm(Base):
    """Film membership and ordering within a collection."""

    collection_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('collection.id', ondelete='CASCADE'),
        nullable=False,
    )
    film_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('film.id', ondelete='CASCADE'),
        nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default='0')
    seed_imdb_id: Mapped[str | None] = mapped_column(String(16), nullable=True)

    __table_args__ = (
        UniqueConstraint('collection_id', 'film_id', name='uq_collection_film_collection_film'),
        Index('ix_collection_film_collection_id_sort_order', 'collection_id', 'sort_order'),
    )
