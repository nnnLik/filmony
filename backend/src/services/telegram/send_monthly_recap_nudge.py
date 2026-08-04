"""Build and deliver monthly recap Telegram nudge for one recipient."""

from __future__ import annotations

import datetime as dt
import html
import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.monthly_recap_nudge_state import MonthlyRecapNudgeState
from models.user import User
from services.profile.build_monthly_recap import BuildMonthlyRecapService
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


@dataclass(frozen=True, slots=True)
class RecapNudgePreview:
    total_rated: int
    top_director_name: str | None
    top_country: str | None


def _films_word(count: int) -> str:
    if count % 10 == 1 and count % 100 != 11:
        return 'фильм'
    if 2 <= count % 10 <= 4 and not (12 <= count % 100 <= 14):
        return 'фильма'
    return 'фильмов'


def _render_recap_nudge_html(
    *,
    year: int,
    month: int,
    preview: RecapNudgePreview | None = None,
) -> str:
    month_label = _MONTH_NAMES_RU[month] if 1 <= month <= 12 else str(month)
    lines = [
        f'📊 <b>Твои итоги за {month_label} {year}</b>',
    ]
    if preview is not None and preview.total_rated > 0:
        lines.append(f'📽 {preview.total_rated} {_films_word(preview.total_rated)} за месяц')
        if preview.top_director_name:
            lines.append(f'🎬 {html.escape(preview.top_director_name)}')
        elif preview.top_country:
            lines.append(f'🌍 {html.escape(preview.top_country)}')
    lines.append('Зайди в Filmony и посмотри сводку месяца.')
    lines.append('')
    lines.append(html_recap_deep_link_block(year=year, month=month))
    return '\n'.join(lines)


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

        preview: RecapNudgePreview | None = None
        try:
            recap = await BuildMonthlyRecapService.build(self._session).execute(
                recipient_user_id,
                year=year,
                month=month,
            )
            preview = RecapNudgePreview(
                total_rated=recap.total_rated,
                top_director_name=recap.top_director_name,
                top_country=recap.top_country,
            )
        except BuildMonthlyRecapService.RecapNotFound:
            preview = None

        body = _render_recap_nudge_html(year=year, month=month, preview=preview)
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
