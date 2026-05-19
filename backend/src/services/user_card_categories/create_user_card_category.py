from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_card_category import UserCardCategory


@dataclass
class CreateUserCardCategoryService:
    """Creates a user-owned category name (unique per user, case-sensitive)."""

    _session: AsyncSession

    class DuplicateCategoryNameError(Exception):
        pass

    class CategoryValidationError(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, user_id: UUID, name: str) -> UserCardCategory:
        s = (name or '').strip()
        if s == '':
            raise self.CategoryValidationError('name is required')
        if len(s) > 120:
            raise self.CategoryValidationError('name max length is 120')

        row = UserCardCategory(user_id=user_id, name=s)
        self._session.add(row)
        try:
            await self._session.flush()
        except IntegrityError as e:
            await self._session.rollback()
            raise self.DuplicateCategoryNameError from e
        await self._session.commit()
        await self._session.refresh(row)
        return row
