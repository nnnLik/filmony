from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from models.feed_post import FeedPost

CO_VIEW_FEED_POST_BODY = 'Смотрели вместе'


@dataclass
class CreateCoViewFeedPostService:
    """Creates the co-view feed post referencing the initiator's rated card."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        *,
        initiator_user_id: UUID,
        initiator_rated_card_id: int,
        watch_session_id: UUID,
    ) -> FeedPost:
        post = FeedPost(
            user_id=initiator_user_id,
            body=CO_VIEW_FEED_POST_BODY,
            image_url=None,
            referenced_card_id=initiator_rated_card_id,
            source_comment_id=None,
            watch_session_id=watch_session_id,
        )
        self._session.add(post)
        await self._session.flush()
        return post
