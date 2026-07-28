"""Deliver weekly controversy Telegram digest for one recipient."""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Self
from uuid import UUID

from models.user import User
from models.weekly_controversy_state import WeeklyControversyState
from services.controversy.compute_weekly_controversy import ComputeWeeklyControversyService
from services.controversy.constants import MIN_SPREAD_FOR_TELEGRAM_DIGEST
from services.controversy.upsert_weekly_controversy_state import UpsertWeeklyControversyStateService
from services.controversy.week_bounds import week_start_for_datetime
from services.telegram.build_weekly_controversy_message import BuildWeeklyControversyMessageService
from services.telegram.engagement_delivery import deliver_engagement_html_message
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class WeeklyControversyDeliveryOutcome(StrEnum):
    sent = 'sent'
    skipped_no_telegram = 'skipped_no_telegram'
    skipped_no_controversy = 'skipped_no_controversy'
    skipped_already_sent = 'skipped_already_sent'
    skipped_low_spread = 'skipped_low_spread'


@dataclass(frozen=True, slots=True)
class WeeklyControversyDeliveryResult:
    outcome: WeeklyControversyDeliveryOutcome
    recipient_user_id: UUID


@dataclass
class SendWeeklyControversyTelegramDigestService:
    """Computes, persists, and idempotently sends the weekly controversy digest."""

    _session: AsyncSession
    _compute_svc: ComputeWeeklyControversyService
    _upsert_svc: UpsertWeeklyControversyStateService
    _message_svc: BuildWeeklyControversyMessageService

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(
            _session=session,
            _compute_svc=ComputeWeeklyControversyService.build(session),
            _upsert_svc=UpsertWeeklyControversyStateService.build(session),
            _message_svc=BuildWeeklyControversyMessageService.build(),
        )

    async def execute(
        self,
        *,
        recipient_user_id: UUID,
        now: dt.datetime | None = None,
    ) -> WeeklyControversyDeliveryResult:
        if now is None:
            now = dt.datetime.now(tz=dt.UTC)
        elif now.tzinfo is None:
            now = now.replace(tzinfo=dt.UTC)
        else:
            now = now.astimezone(dt.UTC)

        recipient = await self._session.get(User, recipient_user_id)
        if recipient is None or recipient.telegram_user_id is None:
            return WeeklyControversyDeliveryResult(
                outcome=WeeklyControversyDeliveryOutcome.skipped_no_telegram,
                recipient_user_id=recipient_user_id,
            )

        week_start = week_start_for_datetime(now)
        existing = (
            await self._session.execute(
                select(WeeklyControversyState).where(
                    WeeklyControversyState.user_id == recipient_user_id,
                    WeeklyControversyState.week_start == week_start,
                )
            )
        ).scalar_one_or_none()
        if existing is not None and existing.sent_at is not None:
            return WeeklyControversyDeliveryResult(
                outcome=WeeklyControversyDeliveryOutcome.skipped_already_sent,
                recipient_user_id=recipient_user_id,
            )

        bundle = await self._compute_svc.execute(
            viewer_user_id=recipient_user_id,
            now=now,
        )
        if bundle is None:
            await self._upsert_svc.execute(
                user_id=recipient_user_id,
                week_start=week_start,
                controversy=None,
                sent_at=now,
            )
            await self._session.commit()
            return WeeklyControversyDeliveryResult(
                outcome=WeeklyControversyDeliveryOutcome.skipped_no_controversy,
                recipient_user_id=recipient_user_id,
            )

        primary = bundle.primary
        if primary.spread < MIN_SPREAD_FOR_TELEGRAM_DIGEST:
            await self._upsert_svc.execute(
                user_id=recipient_user_id,
                week_start=week_start,
                controversy=primary,
                sent_at=now,
            )
            await self._session.commit()
            return WeeklyControversyDeliveryResult(
                outcome=WeeklyControversyDeliveryOutcome.skipped_low_spread,
                recipient_user_id=recipient_user_id,
            )

        payload = self._message_svc.execute(
            bundle=bundle,
            recipient_user_id=recipient_user_id,
            week_start=week_start,
        )
        await deliver_engagement_html_message(
            int(recipient.telegram_user_id),
            payload.html,
            reply_markup=payload.reply_markup,
        )

        await self._upsert_svc.execute(
            user_id=recipient_user_id,
            week_start=week_start,
            controversy=primary,
            sent_at=now,
        )
        await self._session.commit()

        return WeeklyControversyDeliveryResult(
            outcome=WeeklyControversyDeliveryOutcome.sent,
            recipient_user_id=recipient_user_id,
        )


async def run_weekly_controversy_digest_for_recipient_safe(
    *,
    recipient_user_id: UUID,
) -> WeeklyControversyDeliveryResult:
    from core.database import disposable_async_session

    try:
        async with disposable_async_session() as session:
            return await SendWeeklyControversyTelegramDigestService.build(session).execute(
                recipient_user_id=recipient_user_id,
            )
    except Exception:
        logger.exception(
            'weekly controversy digest failed recipient=%s',
            recipient_user_id,
        )
        return WeeklyControversyDeliveryResult(
            outcome=WeeklyControversyDeliveryOutcome.skipped_no_controversy,
            recipient_user_id=recipient_user_id,
        )
