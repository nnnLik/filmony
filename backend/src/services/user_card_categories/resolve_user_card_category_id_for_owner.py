from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_card_category import UserCardCategory
from services.user_card_categories.ensure_default_user_card_category import (
    EnsureDefaultUserCardCategoryService,
)


@dataclass
class ResolveUserCardCategoryIdForOwnerService:
    """Resolves ``category_id`` for card mutations: default shelf or an owned category id."""

    _session: AsyncSession

    class CategoryNotFoundForUserError(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, owner_user_id: UUID, category_id: int | None) -> int:
        if category_id is None:
            return await EnsureDefaultUserCardCategoryService.build(self._session).execute(
                owner_user_id
            )
        row = (
            await self._session.execute(
                select(UserCardCategory.id).where(
                    UserCardCategory.id == category_id,
                    UserCardCategory.user_id == owner_user_id,
                )
            )
        ).scalar_one_or_none()
        if row is None:
            raise self.CategoryNotFoundForUserError
        return int(row)
