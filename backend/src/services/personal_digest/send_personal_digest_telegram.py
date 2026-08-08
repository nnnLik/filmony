"""Build and deliver monthly personal digest Telegram message for one recipient."""

from __future__ import annotations

import datetime as dt
import hashlib
import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.personal_digest_delivery_state import PersonalDigestDeliveryState
from models.user import User
from services.personal_digest.build_personal_digest import (
    BuildPersonalDigestService,
    PersonalDigestDTO,
)
from services.personal_digest.render_personal_digest_telegram import (
    RenderPersonalDigestTelegramService,
)
from services.personal_digest.week_bounds import previous_complete_iso_week
from services.profile.build_monthly_recap import (
    BuildMonthlyRecapService,
    month_period_key,
)
from services.telegram.send_bot_message import SendTelegramBotMessageService

logger = logging.getLogger(__name__)


class DigestDeliveryOutcome(StrEnum):
    sent = 'sent'
    skipped_no_telegram = 'skipped_no_telegram'
    skipped_already_sent = 'skipped_already_sent'
    skipped_no_recap = 'skipped_no_recap'
    skipped_chat_unavailable = 'skipped_chat_unavailable'
    delivery_failed = 'delivery_failed'


@dataclass(frozen=True, slots=True)
class DigestDeliveryResult:
    outcome: DigestDeliveryOutcome
    recipient_user_id: UUID


def _digest_payload_hash(body: str) -> str:
    return hashlib.sha256(body.encode('utf-8')).hexdigest()


@dataclass
class SendPersonalDigestTelegramService:
    """Sends monthly personal digest teaser with idempotent delivery state."""

    _session: AsyncSession
    _send_svc: SendTelegramBotMessageService
    _render_svc: RenderPersonalDigestTelegramService

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(
            _session=session,
            _send_svc=SendTelegramBotMessageService.build(),
            _render_svc=RenderPersonalDigestTelegramService.build(),
        )

    async def execute(
        self,
        *,
        recipient_user_id: UUID,
        year: int,
        month: int,
        now: dt.datetime | None = None,
    ) -> DigestDeliveryResult:
        if now is None:
            now = dt.datetime.now(tz=dt.UTC)

        period_key = month_period_key(year=year, month=month)
        recipient = await self._session.get(User, recipient_user_id)
        if recipient is None or recipient.telegram_user_id is None:
            return DigestDeliveryResult(
                outcome=DigestDeliveryOutcome.skipped_no_telegram,
                recipient_user_id=recipient_user_id,
            )

        existing = (
            await self._session.execute(
                select(PersonalDigestDeliveryState.id).where(
                    PersonalDigestDeliveryState.user_id == recipient_user_id,
                    PersonalDigestDeliveryState.period == 'month',
                    PersonalDigestDeliveryState.period_key == period_key,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return DigestDeliveryResult(
                outcome=DigestDeliveryOutcome.skipped_already_sent,
                recipient_user_id=recipient_user_id,
            )

        try:
            recap = await BuildMonthlyRecapService.build(self._session).execute(
                recipient_user_id,
                year=year,
                month=month,
            )
        except BuildMonthlyRecapService.RecapNotFound:
            return DigestDeliveryResult(
                outcome=DigestDeliveryOutcome.skipped_no_recap,
                recipient_user_id=recipient_user_id,
            )

        body = self._render_svc.execute(recap)
        try:
            await self._send_svc.execute(
                int(recipient.telegram_user_id),
                body,
                parse_mode='HTML',
            )
        except SendTelegramBotMessageService.TelegramChatUnavailable:
            return DigestDeliveryResult(
                outcome=DigestDeliveryOutcome.skipped_chat_unavailable,
                recipient_user_id=recipient_user_id,
            )
        except SendTelegramBotMessageService.TelegramDeliveryFailed:
            logger.warning(
                'monthly personal digest delivery failed recipient=%s',
                recipient_user_id,
            )
            return DigestDeliveryResult(
                outcome=DigestDeliveryOutcome.delivery_failed,
                recipient_user_id=recipient_user_id,
            )

        self._session.add(
            PersonalDigestDeliveryState(
                user_id=recipient_user_id,
                period='month',
                period_key=period_key,
                sent_at=now,
                payload_hash=_digest_payload_hash(body),
            )
        )
        await self._session.commit()
        return DigestDeliveryResult(
            outcome=DigestDeliveryOutcome.sent,
            recipient_user_id=recipient_user_id,
        )

    async def execute_weekly(
        self,
        *,
        recipient_user_id: UUID,
        period_key: str,
        now: dt.datetime | None = None,
    ) -> DigestDeliveryResult:
        if now is None:
            now = dt.datetime.now(tz=dt.UTC)

        recipient = await self._session.get(User, recipient_user_id)
        if recipient is None or recipient.telegram_user_id is None:
            return DigestDeliveryResult(
                outcome=DigestDeliveryOutcome.skipped_no_telegram,
                recipient_user_id=recipient_user_id,
            )

        existing = (
            await self._session.execute(
                select(PersonalDigestDeliveryState.id).where(
                    PersonalDigestDeliveryState.user_id == recipient_user_id,
                    PersonalDigestDeliveryState.period == 'week',
                    PersonalDigestDeliveryState.period_key == period_key,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return DigestDeliveryResult(
                outcome=DigestDeliveryOutcome.skipped_already_sent,
                recipient_user_id=recipient_user_id,
            )

        try:
            digest = await BuildPersonalDigestService.build(self._session).execute(
                recipient_user_id,
                period='week',
                period_key=period_key,
            )
        except BuildPersonalDigestService.DigestNotFound:
            return DigestDeliveryResult(
                outcome=DigestDeliveryOutcome.skipped_no_recap,
                recipient_user_id=recipient_user_id,
            )

        if digest.total_rated <= 0:
            return DigestDeliveryResult(
                outcome=DigestDeliveryOutcome.skipped_no_recap,
                recipient_user_id=recipient_user_id,
            )

        return await self._send_weekly_digest(
            recipient=recipient,
            recipient_user_id=recipient_user_id,
            period_key=period_key,
            digest=digest,
            now=now,
        )

    async def _send_weekly_digest(
        self,
        *,
        recipient: User,
        recipient_user_id: UUID,
        period_key: str,
        digest: PersonalDigestDTO,
        now: dt.datetime,
    ) -> DigestDeliveryResult:
        body = self._render_svc.execute_weekly(digest)
        try:
            await self._send_svc.execute(
                int(recipient.telegram_user_id),
                body,
                parse_mode='HTML',
            )
        except SendTelegramBotMessageService.TelegramChatUnavailable:
            return DigestDeliveryResult(
                outcome=DigestDeliveryOutcome.skipped_chat_unavailable,
                recipient_user_id=recipient_user_id,
            )
        except SendTelegramBotMessageService.TelegramDeliveryFailed:
            logger.warning(
                'weekly personal digest delivery failed recipient=%s',
                recipient_user_id,
            )
            return DigestDeliveryResult(
                outcome=DigestDeliveryOutcome.delivery_failed,
                recipient_user_id=recipient_user_id,
            )

        self._session.add(
            PersonalDigestDeliveryState(
                user_id=recipient_user_id,
                period='week',
                period_key=period_key,
                sent_at=now,
                payload_hash=_digest_payload_hash(body),
            )
        )
        await self._session.commit()
        return DigestDeliveryResult(
            outcome=DigestDeliveryOutcome.sent,
            recipient_user_id=recipient_user_id,
        )


async def run_weekly_personal_digest_for_recipient_safe(
    *,
    recipient_user_id: UUID,
    period_key: str,
) -> DigestDeliveryResult:
    from core.database import disposable_async_session

    try:
        async with disposable_async_session() as session:
            return await SendPersonalDigestTelegramService.build(session).execute_weekly(
                recipient_user_id=recipient_user_id,
                period_key=period_key,
            )
    except Exception:
        logger.exception(
            'weekly personal digest failed recipient=%s period_key=%s',
            recipient_user_id,
            period_key,
        )
        return DigestDeliveryResult(
            outcome=DigestDeliveryOutcome.delivery_failed,
            recipient_user_id=recipient_user_id,
        )


async def run_monthly_personal_digest_for_recipient_safe(
    *,
    recipient_user_id: UUID,
    year: int,
    month: int,
) -> DigestDeliveryResult:
    from core.database import disposable_async_session

    try:
        async with disposable_async_session() as session:
            return await SendPersonalDigestTelegramService.build(session).execute(
                recipient_user_id=recipient_user_id,
                year=year,
                month=month,
            )
    except Exception:
        logger.exception(
            'monthly personal digest failed recipient=%s year=%s month=%s',
            recipient_user_id,
            year,
            month,
        )
        return DigestDeliveryResult(
            outcome=DigestDeliveryOutcome.delivery_failed,
            recipient_user_id=recipient_user_id,
        )
