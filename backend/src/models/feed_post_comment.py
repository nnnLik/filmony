from __future__ import annotations

from uuid import UUID

from sqlalchemy import ForeignKey, Index, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class FeedPostComment(Base):
    feed_post_id: Mapped[int] = mapped_column(
        ForeignKey('feed_post.id', ondelete='CASCADE'),
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
        ForeignKey('feed_post_comment.id', ondelete='CASCADE'),
        nullable=True,
        index=True,
    )
    text: Mapped[str] = mapped_column(String(250), nullable=False)

    __table_args__ = (
        Index(
            'ix_feed_post_comment_post_parent_id',
            'feed_post_id',
            'parent_comment_id',
            'id',
        ),
    )
