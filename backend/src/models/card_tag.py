from __future__ import annotations

from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CardTag(Base):
    """Free-form tag on a user card."""

    card_id: Mapped[int] = mapped_column(
        ForeignKey('user_card.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    tag: Mapped[str] = mapped_column(String(40), nullable=False)

    __table_args__ = (UniqueConstraint('card_id', 'tag', name='uq_card_tag_card_id_tag'),)
