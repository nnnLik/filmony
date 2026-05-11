from __future__ import annotations

from typing import Self

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.feed_post import FeedPost


class FeedPostNotFoundError(Exception):
    pass


class GetFeedPostByIdService:
    """Возвращает пост ленты по id для отдачи в API (чтение любым аутентифицированным пользователем)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(session=session)

    async def execute(self, post_id: int) -> FeedPost:
        row = (
            await self._session.execute(select(FeedPost).where(FeedPost.id == post_id))
        ).scalar_one_or_none()
        if row is None:
            raise FeedPostNotFoundError
        return row
