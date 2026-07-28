"""Persist weekly controversy selection for digest idempotency."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from models.weekly_controversy_state import WeeklyControversyState
from services.controversy.compute_weekly_controversy import WeeklyControversyResult
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class UpsertWeeklyControversyStateService:
    """Creates or updates the weekly controversy row for one user and week."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        *,
        user_id: UUID,
        week_start: dt.date,
        controversy: WeeklyControversyResult | None,
        sent_at: dt.datetime | None = None,
    ) -> WeeklyControversyState:
        row = (
            await self._session.execute(
                select(WeeklyControversyState).where(
                    WeeklyControversyState.user_id == user_id,
                    WeeklyControversyState.week_start == week_start,
                )
            )
        ).scalar_one_or_none()
        if row is None:
            row = WeeklyControversyState(user_id=user_id, week_start=week_start)
            self._session.add(row)

        if controversy is None:
            row.anchor_film_id = None
            row.anchor_catalog_item_id = None
            row.title = None
            row.spread = None
            row.rater_count = None
            row.min_rating = None
            row.max_rating = None
            row.link_card_id = None
        else:
            row.anchor_film_id = controversy.anchor_film_id
            row.anchor_catalog_item_id = controversy.anchor_catalog_item_id
            row.title = controversy.title
            row.spread = controversy.spread
            row.rater_count = controversy.rater_count
            row.min_rating = controversy.min_rating
            row.max_rating = controversy.max_rating
            row.link_card_id = controversy.link_card_id

        if sent_at is not None:
            row.sent_at = sent_at

        await self._session.flush()
        return row
