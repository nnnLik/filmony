from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from models.feed_post import FeedPost


@dataclass
class CreateWatchlistFeedPostService:
    """Creates a feed post for a watchlist entry referencing a planned user card."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, *, user_id: UUID, referenced_user_card_id: int) -> FeedPost:
        post = FeedPost(
            user_id=user_id,
            body='',
            image_url=None,
            referenced_card_id=referenced_user_card_id,
            source_comment_id=None,
        )
        self._session.add(post)
        await self._session.flush()
        return post
