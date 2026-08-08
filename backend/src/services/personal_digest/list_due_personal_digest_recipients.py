"""List users eligible for personal digest Telegram delivery."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Self
from uuid import UUID

from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.personal_digest_delivery_state import PersonalDigestDeliveryState
from models.user import User
from models.user_card import UserCard
from services.personal_digest.week_bounds import (
    parse_iso_week_period_key,
    week_bounds_for_iso_week,
)
from services.profile.build_monthly_recap import (
    _completion_timestamp,
    _month_bounds,
    month_period_key,
)


def _parse_month_period_key(period_key: str) -> tuple[int, int]:
    year_str, month_str = period_key.split('-', maxsplit=1)
    return int(year_str), int(month_str)


@dataclass
class ListDuePersonalDigestRecipientIdsService:
    """Returns user ids with Telegram linked, period activity, and no prior digest send."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        *,
        period: Literal['week', 'month'],
        period_key: str | None = None,
        year: int | None = None,
        month: int | None = None,
    ) -> list[UUID]:
        if period == 'week':
            if period_key is None:
                raise ValueError('week digest requires period_key')
            iso_year, iso_week = parse_iso_week_period_key(period_key)
            resolved_period_key = period_key
            week_start, week_end = week_bounds_for_iso_week(
                iso_year=iso_year,
                iso_week=iso_week,
            )
            rated_in_window = exists(
                select(1).where(
                    UserCard.user_id == User.id,
                    UserCard.is_planned.is_(False),
                    _completion_timestamp() >= week_start,
                    _completion_timestamp() < week_end,
                )
            )
            already_sent = exists(
                select(1).where(
                    PersonalDigestDeliveryState.user_id == User.id,
                    PersonalDigestDeliveryState.period == period,
                    PersonalDigestDeliveryState.period_key == resolved_period_key,
                )
            )
            stmt = (
                select(User.id)
                .where(User.telegram_user_id.isnot(None))
                .where(rated_in_window)
                .where(~already_sent)
                .order_by(User.id.asc())
            )
            return list((await self._session.execute(stmt)).scalars().all())

        if year is not None and month is not None:
            resolved_period_key = month_period_key(year=year, month=month)
        elif period_key is not None:
            resolved_period_key = period_key
            year, month = _parse_month_period_key(period_key)
        else:
            raise ValueError('month digest requires period_key or year/month')

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
                PersonalDigestDeliveryState.user_id == User.id,
                PersonalDigestDeliveryState.period == period,
                PersonalDigestDeliveryState.period_key == resolved_period_key,
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
