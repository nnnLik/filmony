"""Load or compute the viewer's controversial title for the current calendar week."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.weekly_controversy_state import WeeklyControversyState
from services.controversy.compute_weekly_controversy import (
    ComputeWeeklyControversyService,
    WeeklyControversyResult,
)
from services.controversy.week_bounds import week_start_for_datetime


@dataclass(frozen=True, slots=True)
class CurrentWeekControversy:
    week_start: dt.date
    controversy: WeeklyControversyResult | None


@dataclass
class GetCurrentWeekControversyService:
    """Returns persisted or freshly computed controversy for the current ISO week."""

    _session: AsyncSession
    _compute_svc: ComputeWeeklyControversyService

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(
            _session=session,
            _compute_svc=ComputeWeeklyControversyService.build(session),
        )

    async def execute(
        self,
        *,
        viewer_user_id: UUID,
        now: dt.datetime | None = None,
    ) -> CurrentWeekControversy:
        if now is None:
            now = dt.datetime.now(tz=dt.UTC)
        week_start = week_start_for_datetime(now)
        stored = await self._load_state(viewer_user_id=viewer_user_id, week_start=week_start)
        if stored is not None and stored.title is not None and stored.spread is not None:
            return CurrentWeekControversy(
                week_start=week_start,
                controversy=WeeklyControversyResult(
                    anchor_film_id=stored.anchor_film_id,
                    anchor_catalog_item_id=stored.anchor_catalog_item_id,
                    title=stored.title,
                    spread=float(stored.spread),
                    rater_count=int(stored.rater_count or 0),
                    min_rating=float(stored.min_rating or 0),
                    max_rating=float(stored.max_rating or 0),
                    link_card_id=stored.link_card_id,
                ),
            )

        computed = await self._compute_svc.execute(viewer_user_id=viewer_user_id, now=now)
        controversy = computed.primary if computed is not None else None
        return CurrentWeekControversy(week_start=week_start, controversy=controversy)

    async def _load_state(
        self,
        *,
        viewer_user_id: UUID,
        week_start: dt.date,
    ) -> WeeklyControversyState | None:
        return (
            await self._session.execute(
                select(WeeklyControversyState).where(
                    WeeklyControversyState.user_id == viewer_user_id,
                    WeeklyControversyState.week_start == week_start,
                )
            )
        ).scalar_one_or_none()
