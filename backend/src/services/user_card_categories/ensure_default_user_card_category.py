from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_card_category import DEFAULT_USER_CARD_CATEGORY_NAME, UserCardCategory


@dataclass
class EnsureDefaultUserCardCategoryService:
    """Ensures the owner has the default shelf ``Фильмы`` and returns its id."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, user_id: UUID) -> int:
        stmt = (
            pg_insert(UserCardCategory)
            .values(user_id=user_id, name=DEFAULT_USER_CARD_CATEGORY_NAME)
            .on_conflict_do_nothing(index_elements=['user_id', 'name'])
            .returning(UserCardCategory.id)
        )
        new_id = (await self._session.execute(stmt)).scalar_one_or_none()
        if new_id is not None:
            return int(new_id)
        existing = (
            await self._session.execute(
                select(UserCardCategory.id).where(
                    UserCardCategory.user_id == user_id,
                    UserCardCategory.name == DEFAULT_USER_CARD_CATEGORY_NAME,
                )
            )
        ).scalar_one()
        return int(existing)
