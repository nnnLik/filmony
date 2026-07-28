from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_card_category import UserCardCategory
from services.user_card_categories.ensure_default_user_card_category import (
    EnsureDefaultUserCardCategoryService,
)


@dataclass(frozen=True, slots=True)
class UserCardCategoryListRow:
    id: int
    name: str
    created_at: dt.datetime


@dataclass
class ListMyUserCardCategoriesService:
    """Lists the current user's card categories for shelf UI."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, user_id: UUID) -> list[UserCardCategoryListRow]:
        await EnsureDefaultUserCardCategoryService.build(self._session).execute(user_id)
        rows = (
            (
                await self._session.execute(
                    select(UserCardCategory)
                    .where(UserCardCategory.user_id == user_id)
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
