from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_card_category import UserCardCategory


@dataclass
class RenameUserCardCategoryService:
    """Renames a category owned by the given user."""

    _session: AsyncSession

    class CategoryNotFoundError(Exception):
        pass

    class DuplicateCategoryNameError(Exception):
        pass

    class CategoryValidationError(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, user_id: UUID, category_id: int, new_name: str) -> UserCardCategory:
        s = (new_name or '').strip()
        if s == '':
            raise self.CategoryValidationError('name is required')
        if len(s) > 120:
            raise self.CategoryValidationError('name max length is 120')

        row = (
            await self._session.execute(
                select(UserCardCategory).where(
                    UserCardCategory.id == category_id,
                    UserCardCategory.user_id == user_id,
                )
            )
        ).scalar_one_or_none()
        if row is None:
            raise self.CategoryNotFoundError

        row.name = s
        try:
            await self._session.commit()
        except IntegrityError as e:
            await self._session.rollback()
            raise self.DuplicateCategoryNameError from e
        await self._session.refresh(row)
        return row
