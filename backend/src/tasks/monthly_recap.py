"""Celery tasks: monthly recap Telegram nudges.

Beat schedule (document only — configure externally):
    send_monthly_recap_nudges: 1st day of month 10:00 UTC (crontab minute=0 hour=10 day_of_month=1)
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import datetime as dt
import logging

from celery import Celery

from services.profile.build_monthly_recap import previous_complete_month
from services.telegram.send_monthly_recap_nudge import run_monthly_recap_nudge_for_recipient_safe

logger = logging.getLogger(__name__)


def _run_async_isolated(coro) -> None:
    def _runner() -> None:
        asyncio.run(coro)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(_runner)
        fut.result(timeout=120)


async def _send_monthly_recap_nudges_batch_async() -> None:
    from core.database import disposable_async_session
    from services.telegram.list_due_monthly_recap_nudge_recipients import (
        ListDueMonthlyRecapNudgeRecipientIdsService,
    )

    now = dt.datetime.now(tz=dt.UTC)
    year, month = previous_complete_month(now=now)
    async with disposable_async_session() as session:
        recipient_ids = await ListDueMonthlyRecapNudgeRecipientIdsService.build(session).execute(
            year=year,
            month=month,
        )

    for recipient_id in recipient_ids:
        try:
            await run_monthly_recap_nudge_for_recipient_safe(
                recipient_user_id=recipient_id,
                year=year,
                month=month,
            )
        except Exception:
            logger.exception(
                'monthly recap nudge batch failed recipient=%s',
                recipient_id,
            )


def register_tasks(app: Celery) -> None:
    @app.task(name='tasks.monthly_recap.send_monthly_recap_nudges')
    def send_monthly_recap_nudges_task() -> None:
        try:
            _run_async_isolated(_send_monthly_recap_nudges_batch_async())
        except Exception:
            logger.exception('celery task send_monthly_recap_nudges_task failed')
