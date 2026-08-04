from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.feed_post import FeedPost
from services.feed_posts.get_feed_post_by_id import FeedPostNotFoundError
from services.feed_posts.update_feed_post import FeedPostForbiddenError


@dataclass
class DeleteFeedPostService:
    """Hard-deletes a feed post and its comments (DB CASCADE); author-only."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        feed_post_id: int,
        actor_user_id: UUID,
    ) -> None:
        post = (
            await self._session.execute(select(FeedPost).where(FeedPost.id == feed_post_id))
        ).scalar_one_or_none()
        if post is None:
            raise FeedPostNotFoundError
        if post.user_id != actor_user_id:
            raise FeedPostForbiddenError

        await self._session.delete(post)
        await self._session.commit()
