from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from models.watch_session import WatchSession
from models.watch_session_enums import WatchSessionStatus
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


def _parse_participant_ids(raw: list) -> list[UUID]:
    out: list[UUID] = []
    for item in raw or []:
        try:
            out.append(UUID(str(item)))
        except (TypeError, ValueError):
            continue
    return out


@dataclass
class RecordWatchSessionRatingService:
    """Marks co-view progress when a participant upgrades a planned card to rated."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        *,
        user_id: UUID,
        film_id: int | None,
        catalog_item_id: int | None,
        rated_at: dt.datetime,
    ) -> list[UUID]:
        if film_id is None and catalog_item_id is None:
            return []

        if rated_at.tzinfo is None:
            rated_at = rated_at.replace(tzinfo=dt.UTC)
        else:
            rated_at = rated_at.astimezone(dt.UTC)

        if film_id is not None:
            stmt = select(WatchSession).where(
                WatchSession.status == WatchSessionStatus.planned,
                WatchSession.anchor_film_id == film_id,
            )
        else:
            assert catalog_item_id is not None
            stmt = select(WatchSession).where(
                WatchSession.status == WatchSessionStatus.planned,
                WatchSession.anchor_catalog_item_id == catalog_item_id,
            )

        sessions = (await self._session.execute(stmt)).scalars().all()
        touched: list[UUID] = []
        for session in sessions:
            participants = _parse_participant_ids(session.participant_user_ids)
            if user_id not in participants:
                continue
            if session.first_rated_at is None:
                session.first_rated_at = rated_at
            touched.append(session.id)
        if touched:
            await self._session.flush()
        return touched
