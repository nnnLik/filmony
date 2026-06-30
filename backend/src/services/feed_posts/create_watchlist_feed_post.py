from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from models.feed_post import FeedPost


@dataclass
class CreateWatchlistFeedPostService:
    """Creates a minimal feed post for a watchlist entry."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, *, user_id: UUID, card_id: str, provider_meta: dict) -> FeedPost:
        body = f'Added to watchlist: {card_id}'
        post = FeedPost(
            user_id=user_id,
            body=body,
            image_url=None,
            referenced_card_id=None,
            source_comment_id=None,
        )
        self._session.add(post)
        await self._session.flush()
        return post
