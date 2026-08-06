from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.collection import Collection
from models.user_collection_pin import UserCollectionPin


@dataclass
class UnpinCollectionService:
    """Removes a collection pin from the user's profile (idempotent)."""

    _session: AsyncSession

    class CollectionNotFound(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, user_id: UUID, slug: str) -> None:
        collection = (
            await self._session.execute(select(Collection).where(Collection.slug == slug))
        ).scalar_one_or_none()
        if collection is None:
            raise self.CollectionNotFound

        await self._session.execute(
            delete(UserCollectionPin).where(
                UserCollectionPin.user_id == user_id,
                UserCollectionPin.collection_id == collection.id,
            )
        )
        await self._session.commit()
