"""Build and deliver monthly recap Telegram nudge for one recipient."""

from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.monthly_recap_nudge_state import MonthlyRecapNudgeState
from models.user import User
from services.telegram.mini_app_link import html_recap_deep_link_block
from services.telegram.send_bot_message import SendTelegramBotMessageService

logger = logging.getLogger(__name__)

_MONTH_NAMES_RU = (
    '',
    'январь',
    'февраль',
    'март',
    'апрель',
    'май',
    'июнь',
    'июль',
    'август',
    'сентябрь',
    'октябрь',
    'ноябрь',
    'декабрь',
)


class RecapNudgeOutcome(StrEnum):
    sent = 'sent'
    skipped_no_telegram = 'skipped_no_telegram'
    skipped_already_sent = 'skipped_already_sent'
    skipped_chat_unavailable = 'skipped_chat_unavailable'
    delivery_failed = 'delivery_failed'


@dataclass(frozen=True, slots=True)
class RecapNudgeResult:
    outcome: RecapNudgeOutcome
    recipient_user_id: UUID


def _render_recap_nudge_html(*, year: int, month: int) -> str:
    month_label = _MONTH_NAMES_RU[month] if 1 <= month <= 12 else str(month)
    return (
        f'📊 <b>Твои итоги за {month_label} {year}</b>\n'
        f'Зайди в Filmony и посмотри сводку месяца.\n\n'
        f'{html_recap_deep_link_block(year=year, month=month)}'
    )


@dataclass
class SendMonthlyRecapTelegramNudgeService:
    """Sends a short monthly recap nudge with mini-app deep link."""

    _session: AsyncSession
    _send_svc: SendTelegramBotMessageService

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session, _send_svc=SendTelegramBotMessageService.build())

    async def execute(
        self,
        *,
        recipient_user_id: UUID,
        year: int,
        month: int,
        now: dt.datetime | None = None,
    ) -> RecapNudgeResult:
        if now is None:
            now = dt.datetime.now(tz=dt.UTC)

        recipient = await self._session.get(User, recipient_user_id)
        if recipient is None or recipient.telegram_user_id is None:
            return RecapNudgeResult(
                outcome=RecapNudgeOutcome.skipped_no_telegram,
                recipient_user_id=recipient_user_id,
            )

        existing = (
            await self._session.execute(
                select(MonthlyRecapNudgeState.id).where(
                    MonthlyRecapNudgeState.user_id == recipient_user_id,
                    MonthlyRecapNudgeState.year == year,
                    MonthlyRecapNudgeState.month == month,
                )
            )
        ).scalar_one_or_none()
        if existing is not None:
            return RecapNudgeResult(
                outcome=RecapNudgeOutcome.skipped_already_sent,
                recipient_user_id=recipient_user_id,
            )

        body = _render_recap_nudge_html(year=year, month=month)
        try:
            await self._send_svc.execute(
                int(recipient.telegram_user_id),
                body,
                parse_mode='HTML',
            )
        except SendTelegramBotMessageService.TelegramChatUnavailable:
            return RecapNudgeResult(
                outcome=RecapNudgeOutcome.skipped_chat_unavailable,
                recipient_user_id=recipient_user_id,
            )
        except SendTelegramBotMessageService.TelegramDeliveryFailed:
            logger.warning(
                'monthly recap nudge delivery failed recipient=%s',
                recipient_user_id,
            )
            return RecapNudgeResult(
                outcome=RecapNudgeOutcome.delivery_failed,
                recipient_user_id=recipient_user_id,
            )

        self._session.add(
            MonthlyRecapNudgeState(
                user_id=recipient_user_id,
                year=year,
                month=month,
                sent_at=now,
            )
        )
        await self._session.commit()
        return RecapNudgeResult(
            outcome=RecapNudgeOutcome.sent,
            recipient_user_id=recipient_user_id,
        )


async def run_monthly_recap_nudge_for_recipient_safe(
    *,
    recipient_user_id: UUID,
    year: int,
    month: int,
) -> RecapNudgeResult:
    from core.database import disposable_async_session

    try:
        async with disposable_async_session() as session:
            return await SendMonthlyRecapTelegramNudgeService.build(session).execute(
                recipient_user_id=recipient_user_id,
                year=year,
                month=month,
            )
    except Exception:
        logger.exception(
            'monthly recap nudge failed recipient=%s year=%s month=%s',
            recipient_user_id,
            year,
            month,
        )
        return RecapNudgeResult(
            outcome=RecapNudgeOutcome.delivery_failed,
            recipient_user_id=recipient_user_id,
        )
