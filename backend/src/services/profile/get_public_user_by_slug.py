from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


class GetPublicUserBySlugService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, slug: str) -> User | None:
        normalized = slug.strip().lower()
        result = await self._session.execute(select(User).where(User.profile_slug == normalized))
        return result.scalar_one_or_none()
