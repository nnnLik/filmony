from __future__ import annotations

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    SmallInteger,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class FilmActor(Base):
    """Film cast membership with billing order and role."""

    film_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('film.id', ondelete='CASCADE'),
        nullable=False,
    )
    person_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('person.id', ondelete='CASCADE'),
        nullable=False,
    )
    billing_order: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    role: Mapped[str | None] = mapped_column(String(512), nullable=True)

    __table_args__ = (
        UniqueConstraint('film_id', 'person_id', name='uq_film_actor_film_person'),
        UniqueConstraint('film_id', 'billing_order', name='uq_film_actor_film_billing_order'),
        CheckConstraint(
            'billing_order >= 1 AND billing_order <= 10',
            name='ck_film_actor_billing_order_range',
        ),
        Index('ix_film_actor_film_id', 'film_id'),
        Index('ix_film_actor_person_id', 'person_id'),
    )
