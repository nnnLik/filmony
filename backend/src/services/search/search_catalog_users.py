from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from services.search.ilike_escape import escape_ilike_pattern


@dataclass(frozen=True, slots=True)
class CatalogUserSearchHit:
    """Minimal user row for catalog search results (public profile fields)."""

    id: UUID
    profile_slug: str
    username: str | None
    display_name: str | None
    photo_url: str | None


@dataclass
class SearchCatalogUsersService:
    """Finds users by display name, Telegram username, or profile slug substring."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, query: str, limit: int) -> list[CatalogUserSearchHit]:
        pattern = f'%{escape_ilike_pattern(query)}%'
        stmt = (
            select(User)
            .where(
                or_(
                    User.display_name.ilike(pattern, escape='\\'),
                    User.username.ilike(pattern, escape='\\'),
                    User.profile_slug.ilike(pattern, escape='\\'),
                )
            )
            .order_by(User.display_name.asc().nulls_last(), User.profile_slug.asc())
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()
        return [
            CatalogUserSearchHit(
                id=u.id,
                profile_slug=u.profile_slug,
                username=u.username,
                display_name=u.display_name,
                photo_url=u.photo_url,
            )
            for u in rows
        ]
