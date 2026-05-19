from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from services.user_card_categories.ensure_default_user_card_category import (
    EnsureDefaultUserCardCategoryService,
)


async def ensure_default_category(session: AsyncSession, user_id: UUID) -> int:
    return await EnsureDefaultUserCardCategoryService.build(session).execute(user_id)
