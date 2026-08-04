"""List users eligible for monthly recap Telegram nudge."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.monthly_recap_nudge_state import MonthlyRecapNudgeState
from models.user import User
from models.user_card import UserCard
from services.profile.build_monthly_recap import _completion_timestamp, _month_bounds


@dataclass
class ListDueMonthlyRecapNudgeRecipientIdsService:
    """Returns user ids with Telegram linked, month activity, and no prior nudge."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, *, year: int, month: int) -> list[UUID]:
        month_start, month_end = _month_bounds(year, month)
        rated_in_month = exists(
            select(1).where(
                UserCard.user_id == User.id,
                UserCard.is_planned.is_(False),
                _completion_timestamp() >= month_start,
                _completion_timestamp() < month_end,
            )
        )
        already_sent = exists(
            select(1).where(
                MonthlyRecapNudgeState.user_id == User.id,
                MonthlyRecapNudgeState.year == year,
                MonthlyRecapNudgeState.month == month,
            )
        )
        stmt = (
            select(User.id)
            .where(User.telegram_user_id.isnot(None))
            .where(rated_in_month)
            .where(~already_sent)
            .order_by(User.id.asc())
        )
        return list((await self._session.execute(stmt)).scalars().all())
