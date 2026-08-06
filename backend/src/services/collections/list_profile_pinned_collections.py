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
class ListProfilePinnedCollectionsService:
    """Lists profile owner's pinned collections ordered by pin sort_order."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, user_id: UUID) -> list[CollectionSummaryDTO]:
        rows = (
            await self._session.execute(
                select(UserCollectionPin, Collection)
                .join(Collection, Collection.id == UserCollectionPin.collection_id)
                .where(
                    UserCollectionPin.user_id == user_id,
                    Collection.is_active.is_(True),
                )
                .order_by(UserCollectionPin.sort_order.asc(), UserCollectionPin.id.asc())
            )
        ).all()
        if not rows:
            return []

        collection_ids = [int(collection.id) for _, collection in rows]
        progress_rows = (
            (
                await self._session.execute(
                    select(UserCollectionProgress).where(
                        UserCollectionProgress.user_id == user_id,
                        UserCollectionProgress.collection_id.in_(collection_ids),
                    )
                )
            )
            .scalars()
            .all()
        )
        progress_by_collection = {int(row.collection_id): row for row in progress_rows}

        items: list[CollectionSummaryDTO] = []
        for _pin, collection in rows:
            collection_id = int(collection.id)
            progress = progress_by_collection.get(collection_id)
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
            items.append(
                CollectionSummaryDTO(
                    slug=str(collection.slug),
                    kind=collection.kind,
                    title=str(collection.title),
                    description=collection.description,
                    season_year=collection.season_year,
                    film_count=int(collection.film_count),
                    content_updated_at=collection.content_updated_at,
                    viewer_progress=viewer_progress,
                    is_pinned=True,
                )
            )
        return items
