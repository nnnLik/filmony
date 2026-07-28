"""List users due for subscribed-activity Telegram digest delivery."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import exists, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.subscribed_activity_digest_state import SubscribedActivityDigestState
from models.user import User
from models.user_subscription import UserSubscription
from services.telegram.subscribed_activity_digest_candidates import DIGEST_INTERVAL


@dataclass
class ListDueSubscribedActivityDigestRecipientIdsService:
    """Returns user ids eligible for digest processing (subscriptions + Telegram link)."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, *, now: dt.datetime | None = None) -> list[UUID]:
        if now is None:
            now = dt.datetime.now(tz=dt.UTC)
        from services.telegram.subscribed_activity_digest_candidates import _ensure_naive_utc

        now = _ensure_naive_utc(now)
        cutoff = now - DIGEST_INTERVAL

        has_following = exists(select(1).where(UserSubscription.follower_user_id == User.id))

        stmt = (
            select(User.id)
            .outerjoin(
                SubscribedActivityDigestState,
                SubscribedActivityDigestState.recipient_user_id == User.id,
            )
            .where(User.telegram_user_id.isnot(None))
            .where(has_following)
            .where(
                or_(
                    SubscribedActivityDigestState.id.is_(None),
                    SubscribedActivityDigestState.last_processed_at.is_(None),
                    SubscribedActivityDigestState.last_processed_at <= cutoff,
                )
            )
            .order_by(User.id.asc())
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        return list(rows)
