from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, Index, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class FeedPost(Base):
    """Текстовый пост ленты: plain text, опционально одна картинка, опциональная ссылка на карточку."""

    user_id: Mapped[UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey('user.id', ondelete='CASCADE'),
        nullable=False,
        index=True,
    )
    body: Mapped[str] = mapped_column(String(2000), nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    referenced_card_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('user_card.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )
    source_comment_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('card_comment.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )

    __table_args__ = (
        Index(
            'ix_feed_post_user_id_created_at_id',
            'user_id',
            'created_at',
            'id',
            postgresql_ops={'created_at': 'DESC', 'id': 'DESC'},
        ),
    )
