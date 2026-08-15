from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_card import UserCard

HEATMAP_WINDOW_DAYS = 30


@dataclass(frozen=True, slots=True)
class ActivityDistributionItem:
    date: dt.date
    count: int


def heatmap_date_window(today: dt.date) -> tuple[dt.date, dt.date]:
    """Inclusive heatmap window: start = today - (HEATMAP_WINDOW_DAYS - 1)."""
    activity_end = today
    activity_start = today - dt.timedelta(days=HEATMAP_WINDOW_DAYS - 1)
    return activity_start, activity_end


def _completion_timestamp():
    return func.coalesce(UserCard.completed_at, UserCard.created_at)


async def load_user_card_activity_distribution(
    session: AsyncSession,
    *,
    user_id: UUID,
    activity_start: dt.date,
    activity_end: dt.date,
    activity_category_id: int | None,
) -> list[ActivityDistributionItem]:
    completion = _completion_timestamp()
    day_col = func.date(completion).label('day')
    range_start = dt.datetime.combine(activity_start, dt.time.min, tzinfo=dt.UTC)
    range_end_exclusive = dt.datetime.combine(
        activity_end + dt.timedelta(days=1),
        dt.time.min,
        tzinfo=dt.UTC,
    )
    query = (
        select(day_col, func.count(UserCard.id))
        .where(
            UserCard.user_id == user_id,
            UserCard.is_planned.is_(False),
            completion >= range_start,
            completion < range_end_exclusive,
        )
        .group_by(day_col)
        .order_by(day_col)
    )
    if activity_category_id is not None:
        query = query.where(UserCard.category_id == activity_category_id)

    rows = (await session.execute(query)).all()
    return [ActivityDistributionItem(date=day, count=int(count)) for day, count in rows]
