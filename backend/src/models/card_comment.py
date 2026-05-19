from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class CardComment(Base):
    """Comment on a user card; persists in legacy `movie_card_comment` table."""

    __tablename__ = 'movie_card_comment'

    card_id: Mapped[int] = mapped_column(
        'movie_card_id',
        ForeignKey('movie_card.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    parent_comment_id: Mapped[int | None] = mapped_column(
        ForeignKey('movie_card_comment.id', ondelete='CASCADE'),
        nullable=True,
        index=True,
    )
    text: Mapped[str] = mapped_column(String(250), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)

    __table_args__ = (
        Index(
            'ix_movie_card_comment_card_parent_id',
            'movie_card_id',
            'parent_comment_id',
            'id',
        ),
    )
