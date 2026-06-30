from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from models.feed_post import FeedPost
from services.feed_posts.watchlist_provider_snapshot import build_watchlist_provider_snapshot


@dataclass
class CreateWatchlistFeedPostService:
    """Creates a minimal feed post for a watchlist entry."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, *, user_id: UUID, card_id: str, provider_meta: dict) -> FeedPost:
        _ = card_id
        snapshot = build_watchlist_provider_snapshot(provider_meta)
        body = snapshot.title
        if snapshot.description is not None:
            body = f'{snapshot.title}\n\n{snapshot.description}'
        post = FeedPost(
            user_id=user_id,
            body=body,
            image_url=snapshot.poster_url,
            referenced_card_id=None,
            source_comment_id=None,
        )
        self._session.add(post)
        await self._session.flush()
        return post
