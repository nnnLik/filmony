from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.collection import Collection
from models.user_collection_pin import UserCollectionPin
from models.user_collection_progress import UserCollectionProgress
from services.collections.list_collections import CollectionSummaryDTO, UserCollectionProgressDTO


@dataclass
class GetCollectionService:
    """Returns collection header metadata with optional viewer progress and pin state."""

    _session: AsyncSession

    class CollectionNotFound(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        slug: str,
        *,
        viewer_user_id: UUID | None = None,
    ) -> CollectionSummaryDTO:
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

        progress: UserCollectionProgress | None = None
        is_pinned = False
        if viewer_user_id is not None:
            progress = (
                await self._session.execute(
                    select(UserCollectionProgress).where(
                        UserCollectionProgress.user_id == viewer_user_id,
                        UserCollectionProgress.collection_id == collection.id,
                    )
                )
            ).scalar_one_or_none()
            pin = (
                await self._session.execute(
                    select(UserCollectionPin.id).where(
                        UserCollectionPin.user_id == viewer_user_id,
                        UserCollectionPin.collection_id == collection.id,
                    )
                )
            ).scalar_one_or_none()
            is_pinned = pin is not None

        viewer_progress: UserCollectionProgressDTO | None = None
        is_pinned_value: bool | None = None
        if viewer_user_id is not None:
            is_pinned_value = is_pinned
            if progress is not None:
                viewer_progress = UserCollectionProgressDTO(
                    rated_count=int(progress.rated_count),
                    total_count=int(progress.total_count),
                    completed_at=progress.completed_at,
                )
            else:
                viewer_progress = UserCollectionProgressDTO(
                    rated_count=0,
                    total_count=int(collection.film_count),
                    completed_at=None,
                )

        return CollectionSummaryDTO(
            slug=str(collection.slug),
            kind=collection.kind,
            title=str(collection.title),
            description=collection.description,
            season_year=collection.season_year,
            film_count=int(collection.film_count),
            content_updated_at=collection.content_updated_at,
            viewer_progress=viewer_progress,
            is_pinned=is_pinned_value,
        )
