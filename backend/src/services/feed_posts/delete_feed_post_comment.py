from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.feed_post_comment import FeedPostComment


class FeedPostCommentNotFoundError(Exception):
    pass


class FeedPostCommentForbiddenError(Exception):
    pass


class FeedPostCommentMismatchError(Exception):
    pass


@dataclass
class DeleteFeedPostCommentService:
    """Hard-deletes a feed post comment and its reply subtree (DB CASCADE); author-only."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        feed_post_id: int,
        comment_id: int,
        actor_user_id: UUID,
    ) -> None:
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

        await self._session.delete(comment)
        await self._session.commit()
