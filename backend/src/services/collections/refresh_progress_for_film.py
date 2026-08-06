from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.collection_film import CollectionFilm
from services.collections.refresh_user_collection_progress import (
    RefreshUserCollectionProgressService,
)


@dataclass
class RefreshProgressForFilmService:
    """Refresh collection progress for every collection that includes ``film_id``."""

    _session: AsyncSession
    _refresh_progress_service: RefreshUserCollectionProgressService

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(
            _session=session,
            _refresh_progress_service=RefreshUserCollectionProgressService.build(session),
        )

    async def execute(self, user_id: UUID, film_id: int) -> None:
        collection_ids = (
            (
                await self._session.execute(
                    select(CollectionFilm.collection_id).where(CollectionFilm.film_id == film_id)
                )
            )
            .scalars()
            .all()
        )

        for collection_id in collection_ids:
            await self._refresh_progress_service.execute(user_id, int(collection_id))
