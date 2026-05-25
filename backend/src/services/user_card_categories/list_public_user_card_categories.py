from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_card_category import UserCardCategory
from services.user_card_categories.list_my_user_card_categories import UserCardCategoryListRow


@dataclass
class ListPublicUserCardCategoriesService:
    """Lists another user's card categories (shelves) for public profile filtering.

    Read-only — does not create a default shelf; callers that need ensured defaults still use
    `ListMyUserCardCategoriesService` for the current user on owner flows.
    """

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, owner_user_id: UUID) -> list[UserCardCategoryListRow]:
        rows = (
            (
                await self._session.execute(
                    select(UserCardCategory)
                    .where(UserCardCategory.user_id == owner_user_id)
                    .order_by(UserCardCategory.name.asc(), UserCardCategory.id.asc())
                )
            )
            .scalars()
            .all()
        )
        return [
            UserCardCategoryListRow(id=int(r.id), name=r.name, created_at=r.created_at)
            for r in rows
        ]
