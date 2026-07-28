"""List users eligible for weekly controversy Telegram digest."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from models.user_subscription import UserSubscription
from models.weekly_controversy_state import WeeklyControversyState
from services.controversy.week_bounds import week_start_for_datetime


@dataclass
class ListDueWeeklyControversyRecipientIdsService:
    """Users with Telegram linked, at least one follow, digest not yet sent this week."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, *, now: dt.datetime | None = None) -> list[UUID]:
        if now is None:
            now = dt.datetime.now(tz=dt.UTC)
        week_start = week_start_for_datetime(now)
        has_following = exists(select(1).where(UserSubscription.follower_user_id == User.id))

        stmt = (
            select(User.id)
            .outerjoin(
                WeeklyControversyState,
                (WeeklyControversyState.user_id == User.id)
                & (WeeklyControversyState.week_start == week_start),
            )
            .where(User.telegram_user_id.isnot(None))
            .where(has_following)
            .where(
                or_(
                    WeeklyControversyState.id.is_(None),
                    WeeklyControversyState.sent_at.is_(None),
                )
            )
            .order_by(User.id.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return list(rows)
