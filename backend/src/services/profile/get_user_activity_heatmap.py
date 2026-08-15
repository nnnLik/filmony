from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_card import UserCard
from models.user_card_category import UserCardCategory
from services.profile.get_user_card_stats import (
    UNCATEGORIZED_SHELF_NAME,
    CategoryDistributionItem,
)
from services.profile.user_card_activity import (
    ActivityDistributionItem,
    heatmap_date_window,
    load_user_card_activity_distribution,
)


@dataclass(frozen=True, slots=True)
class UserActivityHeatmap:
    activity_distribution: list[ActivityDistributionItem]
    activity_start: dt.date
    activity_end: dt.date
    category_distribution: list[CategoryDistributionItem]


@dataclass
class GetUserActivityHeatmapService:
    """Loads a 30-day completed-card activity heatmap plus all-time shelf counts.

    Used by the profile chrome heatmap so the client does not download full /stats.
    """

    _session: AsyncSession

    class InvalidCategoryFilter(Exception):
        """activity_category_id does not belong to the profile user."""

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        user_id: UUID,
        *,
        activity_category_id: int | None = None,
    ) -> UserActivityHeatmap:
        if activity_category_id is not None:
            owns = (
                await self._session.execute(
                    select(UserCardCategory.id).where(
                        UserCardCategory.id == activity_category_id,
                        UserCardCategory.user_id == user_id,
                    )
                )
            ).scalar_one_or_none()
            if owns is None:
                raise self.InvalidCategoryFilter

        activity_start, activity_end = heatmap_date_window(dt.datetime.now(dt.UTC).date())

        activity_distribution = await load_user_card_activity_distribution(
            self._session,
            user_id=user_id,
            activity_start=activity_start,
            activity_end=activity_end,
            activity_category_id=activity_category_id,
        )

        category_rows = (
            await self._session.execute(
                select(
                    UserCard.category_id,
                    UserCardCategory.name,
                    func.count(UserCard.id),
                )
                .outerjoin(
                    UserCardCategory,
                    (UserCardCategory.id == UserCard.category_id)
                    & (UserCardCategory.user_id == UserCard.user_id),
                )
                .where(UserCard.user_id == user_id, UserCard.is_planned.is_(False))
                .group_by(UserCard.category_id, UserCardCategory.name)
            )
        ).all()

        category_distribution = sorted(
            [
                CategoryDistributionItem(
                    category_id=None,
                    name=UNCATEGORIZED_SHELF_NAME,
                    count=int(count),
                )
                if category_id is None
                else CategoryDistributionItem(
                    category_id=int(category_id),
                    name=str(name),
                    count=int(count),
                )
                for category_id, name, count in category_rows
            ],
            key=lambda item: (-item.count, item.category_id is not None, item.category_id or 0),
        )

        return UserActivityHeatmap(
            activity_distribution=activity_distribution,
            activity_start=activity_start,
            activity_end=activity_end,
            category_distribution=category_distribution,
        )
