from __future__ import annotations

from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User


class AllocateDefaultProfileSlugService:
    """Assign a unique `profile_slug` for a new user (short opaque slug, user may change later)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self) -> str:
        for _ in range(16):
            slug = f'u{uuid4().hex[:12]}'
            res = await self._session.execute(select(User.id).where(User.profile_slug == slug))
            if res.scalar_one_or_none() is None:
                return slug
        msg = 'could not allocate a unique profile_slug'
        raise RuntimeError(msg)
