from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.collection import Collection
from models.collection_film import CollectionFilm
from models.user_collection_pin import UserCollectionPin
from models.user_collection_progress import UserCollectionProgress
from services.collections.list_collections import CollectionSummaryDTO, UserCollectionProgressDTO


@dataclass
class ListFilmCollectionsService:
    """Lists active collections that include a given film, with optional viewer progress."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        film_id: int,
        *,
        viewer_user_id: UUID | None = None,
    ) -> list[CollectionSummaryDTO]:
        query = (
            select(Collection)
            .join(CollectionFilm, CollectionFilm.collection_id == Collection.id)
            .where(
                CollectionFilm.film_id == film_id,
                Collection.is_active.is_(True),
            )
            .order_by(Collection.title.asc(), Collection.id.asc())
        )
        collections = (await self._session.execute(query)).scalars().all()
        if not collections:
            return []

        collection_ids = [int(c.id) for c in collections]

        progress_by_collection: dict[int, UserCollectionProgress] = {}
        pinned_ids: set[int] = set()
        if viewer_user_id is not None:
            progress_rows = (
                (
                    await self._session.execute(
                        select(UserCollectionProgress).where(
                            UserCollectionProgress.user_id == viewer_user_id,
                            UserCollectionProgress.collection_id.in_(collection_ids),
                        )
                    )
                )
                .scalars()
                .all()
            )
            progress_by_collection = {int(row.collection_id): row for row in progress_rows}

            pin_rows = (
                await self._session.execute(
                    select(UserCollectionPin.collection_id).where(
                        UserCollectionPin.user_id == viewer_user_id,
                        UserCollectionPin.collection_id.in_(collection_ids),
                    )
                )
            ).all()
            pinned_ids = {int(row[0]) for row in pin_rows}

        return [
            self._to_dto(
                collection,
                viewer_user_id=viewer_user_id,
                progress=progress_by_collection.get(int(collection.id)),
                is_pinned=int(collection.id) in pinned_ids,
            )
            for collection in collections
        ]

    def _to_dto(
        self,
        collection: Collection,
        *,
        viewer_user_id: UUID | None,
        progress: UserCollectionProgress | None,
        is_pinned: bool,
    ) -> CollectionSummaryDTO:
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
