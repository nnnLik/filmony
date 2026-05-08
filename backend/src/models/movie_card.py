from __future__ import annotations

import datetime as dt
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    false,
    func,
    text,
)
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
        Integer,
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
    is_favorite: Mapped[bool] = mapped_column(
        Boolean(),
        server_default=false(),
        nullable=False,
    )
    favorite_marked_at: Mapped[dt.datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    __table_args__ = (
        UniqueConstraint('user_id', 'film_id', name='uq_movie_card_user_film'),
        Index(
            'ix_movie_card_user_id_created_at_id',
            'user_id',
            'created_at',
            'id',
            postgresql_ops={'created_at': 'DESC', 'id': 'DESC'},
        ),
        Index(
            'ix_movie_card_created_at_id',
            'created_at',
            'id',
            postgresql_ops={'created_at': 'DESC', 'id': 'DESC'},
        ),
        Index(
            'ix_movie_card_user_favorites_order',
            'user_id',
            'favorite_marked_at',
            'id',
            postgresql_ops={'favorite_marked_at': 'DESC NULLS LAST', 'id': 'DESC'},
            postgresql_where=text('is_favorite IS TRUE'),
        ),
    )
