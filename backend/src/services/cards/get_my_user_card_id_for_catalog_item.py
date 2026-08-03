"""Look up the viewer's rated card for a catalog item, if any."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_card import UserCard


@dataclass
class GetMyUserCardIdForCatalogItemService:
    """Returns the viewer's non-planned user card id bound to a catalog item."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, user_id: UUID, catalog_item_id: int) -> int | None:
        row = (
            await self._session.execute(
                select(UserCard.id).where(
                    UserCard.user_id == user_id,
                    UserCard.catalog_item_id == catalog_item_id,
                    UserCard.is_planned.is_(False),
                )
            )
        ).scalar_one_or_none()
        return int(row) if row is not None else None
