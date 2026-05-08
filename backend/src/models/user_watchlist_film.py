from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, Integer, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class UserWatchlistFilm(Base):
    """A film the user marked as «want to watch» (public on profile, no rating)."""

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
    )
    film_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('film.id', ondelete='CASCADE'),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint('user_id', 'film_id', name='uq_user_watchlist_film_user_film'),
    )
