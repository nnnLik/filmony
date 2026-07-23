from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.feed_post_comment import FeedPostComment
from services.cards.comment_reaction_tokens import (
    CommentReactionTokenError,
    validate_comment_text_with_reaction_tokens,
)


class FeedPostCommentNotFoundError(Exception):
    pass


class FeedPostCommentForbiddenError(Exception):
    pass


class FeedPostCommentMismatchError(Exception):
    pass


class FeedPostCommentValidationError(Exception):
    pass


@dataclass
class UpdateFeedPostCommentService:
    """Updates text of a feed post comment; only the comment author may edit."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        feed_post_id: int,
        comment_id: int,
        actor_user_id: UUID,
        text: str,
    ) -> FeedPostComment:
        comment = (
            await self._session.execute(
                select(FeedPostComment).where(FeedPostComment.id == comment_id)
            )
        ).scalar_one_or_none()
        if comment is None:
            raise FeedPostCommentNotFoundError
        if comment.feed_post_id != feed_post_id:
            raise FeedPostCommentMismatchError
        if comment.user_id != actor_user_id:
            raise FeedPostCommentForbiddenError

        try:
            normalized, _ = await validate_comment_text_with_reaction_tokens(
                text, self._session, author_user_id=actor_user_id
            )
        except CommentReactionTokenError as exc:
            raise FeedPostCommentValidationError(str(exc)) from exc

        comment.text = normalized
        await self._session.commit()
        await self._session.refresh(comment)
        return comment
