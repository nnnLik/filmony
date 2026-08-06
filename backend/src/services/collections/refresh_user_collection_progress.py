from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from models.collection_film import CollectionFilm
from models.user_card import UserCard
from models.user_collection_progress import UserCollectionProgress
from services.collections.complete_collection import CompleteCollectionService
from services.collections.meaningful_rated_card import meaningful_rated_card_criteria


def should_mark_collection_completed(
    *,
    rated_count: int,
    total_count: int,
    completed_at: dt.datetime | None,
) -> bool:
    """Return True when a collection should transition to completed for the first time."""
    return total_count > 0 and rated_count >= total_count and completed_at is None


def resolve_completed_at(
    *,
    rated_count: int,
    total_count: int,
    existing_completed_at: dt.datetime | None,
    now: dt.datetime,
) -> dt.datetime | None:
    """Keep ``completed_at`` sticky once set; otherwise set on first 100% transition."""
    if existing_completed_at is not None:
        return existing_completed_at
    if should_mark_collection_completed(
        rated_count=rated_count,
        total_count=total_count,
        completed_at=None,
    ):
        return now
    return None


@dataclass
class RefreshUserCollectionProgressService:
    """Recompute and upsert per-user collection progress from rated cards."""

    _session: AsyncSession
    _complete_collection_service: CompleteCollectionService

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(
            _session=session,
            _complete_collection_service=CompleteCollectionService.build(session),
        )

    async def execute(self, user_id: UUID, collection_id: int) -> UserCollectionProgress:
        total_count = await self._count_total(collection_id)
        rated_count = await self._count_rated(user_id, collection_id)

        existing = await self._get_progress(user_id, collection_id)
        existing_completed_at = existing.completed_at if existing is not None else None
        now = dt.datetime.now(dt.UTC)
        completed_at = resolve_completed_at(
            rated_count=rated_count,
            total_count=total_count,
            existing_completed_at=existing_completed_at,
            now=now,
        )
        newly_completed = existing_completed_at is None and completed_at is not None

        progress = await self._upsert_progress(
            user_id=user_id,
            collection_id=collection_id,
            rated_count=rated_count,
            total_count=total_count,
            completed_at=completed_at,
        )

        if newly_completed:
            await self._complete_collection_service.execute(user_id, collection_id)

        await self._session.commit()
        await self._session.refresh(progress)
        return progress

    async def _count_total(self, collection_id: int) -> int:
        stmt = (
            select(func.count())
            .select_from(CollectionFilm)
            .where(CollectionFilm.collection_id == collection_id)
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def _count_rated(self, user_id: UUID, collection_id: int) -> int:
        stmt = (
            select(func.count(func.distinct(CollectionFilm.film_id)))
            .select_from(CollectionFilm)
            .join(
                UserCard,
                (UserCard.film_id == CollectionFilm.film_id),
            )
            .where(
                CollectionFilm.collection_id == collection_id,
                *meaningful_rated_card_criteria(user_id=user_id),
            )
        )
        return int((await self._session.execute(stmt)).scalar_one())

    async def _get_progress(
        self,
        user_id: UUID,
        collection_id: int,
    ) -> UserCollectionProgress | None:
        return (
            await self._session.execute(
                select(UserCollectionProgress).where(
                    UserCollectionProgress.user_id == user_id,
                    UserCollectionProgress.collection_id == collection_id,
                )
            )
        ).scalar_one_or_none()

    async def _upsert_progress(
        self,
        *,
        user_id: UUID,
        collection_id: int,
        rated_count: int,
        total_count: int,
        completed_at: dt.datetime | None,
    ) -> UserCollectionProgress:
        stmt = (
            pg_insert(UserCollectionProgress)
            .values(
                user_id=user_id,
                collection_id=collection_id,
                rated_count=rated_count,
                total_count=total_count,
                completed_at=completed_at,
            )
            .on_conflict_do_update(
                index_elements=['user_id', 'collection_id'],
                set_={
                    'rated_count': rated_count,
                    'total_count': total_count,
                    'completed_at': completed_at,
                },
            )
            .returning(UserCollectionProgress)
        )
        return (await self._session.execute(stmt)).scalar_one()
