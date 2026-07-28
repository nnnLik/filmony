from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import Date, cast, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_card import UserCard


@dataclass(frozen=True, slots=True)
class UserRatingStreakItem:
    current: int


def compute_current_rating_streak(
    streak_days: set[dt.date],
    *,
    today_utc: dt.date,
) -> int:
    """Count consecutive UTC streak days ending at today or yesterday."""
    if today_utc in streak_days:
        anchor = today_utc
    else:
        anchor = today_utc - dt.timedelta(days=1)

    if anchor not in streak_days:
        return 0

    streak = 0
    day = anchor
    while day in streak_days:
        streak += 1
        day -= dt.timedelta(days=1)
    return streak


@dataclass
class BatchUserRatingStreaksService:
    """Computes current rating streaks for many users from completed card activity."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        user_ids: list[UUID],
        *,
        min_current: int = 0,
        today_utc: dt.date | None = None,
    ) -> dict[UUID, UserRatingStreakItem]:
        unique_ids = list(dict.fromkeys(user_ids))
        if not unique_ids:
            return {}

        streak_day = cast(func.timezone('UTC', UserCard.completed_at), Date)
        rows = (
            await self._session.execute(
                select(UserCard.user_id, streak_day.label('streak_day')).where(
                    UserCard.user_id.in_(unique_ids),
                    UserCard.is_planned.is_(False),
                    UserCard.rating >= 1,
                    UserCard.completed_at.isnot(None),
                ).distinct()
            )
        ).all()

        days_by_user: dict[UUID, set[dt.date]] = {user_id: set() for user_id in unique_ids}
        for user_id, streak_day_value in rows:
            if streak_day_value is not None:
                days_by_user[user_id].add(streak_day_value)

        anchor_day = today_utc or dt.datetime.now(dt.UTC).date()
        out: dict[UUID, UserRatingStreakItem] = {}
        for user_id in unique_ids:
            current = compute_current_rating_streak(days_by_user[user_id], today_utc=anchor_day)
            if current >= min_current:
                out[user_id] = UserRatingStreakItem(current=current)
        return out
