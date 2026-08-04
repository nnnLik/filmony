from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.feed_post import FeedPost
from services.feed_posts.get_feed_post_by_id import FeedPostNotFoundError
from services.feed_posts.validate_feed_post_body import (
    FeedPostBodyValidationError,
    validate_feed_post_body,
)


class FeedPostForbiddenError(Exception):
    pass


class FeedPostUpdateValidationError(Exception):
    pass


@dataclass
class UpdateFeedPostService:
    """Updates body text of a feed post; only the post author may edit.

    Image and card references stay unchanged. Empty body is allowed when the post
    still has an image.
    """

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        feed_post_id: int,
        actor_user_id: UUID,
        body: str,
    ) -> FeedPost:
        post = (
            await self._session.execute(select(FeedPost).where(FeedPost.id == feed_post_id))
        ).scalar_one_or_none()
        if post is None:
            raise FeedPostNotFoundError
        if post.user_id != actor_user_id:
            raise FeedPostForbiddenError

        body_raw = body.strip()
        has_image = post.image_url is not None and post.image_url.strip() != ''
        if body_raw == '' and not has_image:
            raise FeedPostUpdateValidationError('body must not be empty')

        if body_raw == '':
            body_final = ''
        else:
            try:
                body_final, _ = await validate_feed_post_body(
                    body_raw, self._session, author_user_id=actor_user_id
                )
            except FeedPostBodyValidationError as exc:
                raise FeedPostUpdateValidationError(str(exc)) from exc

        post.body = body_final
        await self._session.commit()
        await self._session.refresh(post)
        return post
