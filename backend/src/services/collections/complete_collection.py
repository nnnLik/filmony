from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.collection import Collection
from services.achievements.grant_collection_achievement import GrantCollectionAchievementService


@dataclass
class CompleteCollectionService:
    """Idempotently records collection completion and triggers achievement grant."""

    _session: AsyncSession
    _grant_achievement_service: GrantCollectionAchievementService

    class CollectionNotFoundError(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(
            _session=session,
            _grant_achievement_service=GrantCollectionAchievementService.build(session),
        )

    async def execute(self, user_id: UUID, collection_id: int) -> None:
        collection = (
            await self._session.execute(select(Collection).where(Collection.id == collection_id))
        ).scalar_one_or_none()
        if collection is None:
            raise self.CollectionNotFoundError

        await self._grant_achievement_service.execute(user_id, collection.slug)
