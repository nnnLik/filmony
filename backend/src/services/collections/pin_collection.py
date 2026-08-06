from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.collection import Collection
from models.user_collection_pin import UserCollectionPin

MAX_COLLECTION_PINS = 10


@dataclass
class PinCollectionService:
    """Pins an active collection on the user's profile (max 10 pins)."""

    _session: AsyncSession

    class CollectionNotFound(Exception):
        pass

    class PinLimitExceeded(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, user_id: UUID, slug: str) -> None:
        collection = (
            await self._session.execute(
                select(Collection).where(
                    Collection.slug == slug,
                    Collection.is_active.is_(True),
                )
            )
        ).scalar_one_or_none()
        if collection is None:
            raise self.CollectionNotFound

        collection_id = int(collection.id)
        existing = (
            await self._session.execute(
                select(UserCollectionPin).where(
                    UserCollectionPin.user_id == user_id,
                    UserCollectionPin.collection_id == collection_id,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return

        pin_count = int(
            (
                await self._session.execute(
                    select(func.count())
                    .select_from(UserCollectionPin)
                    .where(UserCollectionPin.user_id == user_id)
                )
            ).scalar_one()
        )
        if pin_count >= MAX_COLLECTION_PINS:
            raise self.PinLimitExceeded

        max_sort = (
            await self._session.execute(
                select(func.max(UserCollectionPin.sort_order)).where(
                    UserCollectionPin.user_id == user_id
                )
            )
        ).scalar_one()
        next_sort = 0 if max_sort is None else int(max_sort) + 1

        self._session.add(
            UserCollectionPin(
                user_id=user_id,
                collection_id=collection_id,
                sort_order=next_sort,
                pinned_at=dt.datetime.now(dt.UTC),
            )
        )
        await self._session.commit()
