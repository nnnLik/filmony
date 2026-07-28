"""Celery tasks: weekly controversy Telegram digests.

Beat schedule (document only — configure externally):
    send_weekly_controversy_digests: Monday 10:00 UTC (crontab minute=0 hour=10 day_of_week=1)
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import datetime as dt
import logging

from celery import Celery
from services.telegram.send_weekly_controversy_digest import (
    run_weekly_controversy_digest_for_recipient_safe,
)

logger = logging.getLogger(__name__)


def _run_async_isolated(coro) -> None:
    def _runner() -> None:
        asyncio.run(coro)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(_runner)
        fut.result(timeout=120)


async def _send_weekly_controversy_digests_batch_async() -> None:
    from core.database import disposable_async_session
    from services.controversy.list_due_weekly_controversy_recipient_ids import (
        ListDueWeeklyControversyRecipientIdsService,
    )

    now = dt.datetime.now(tz=dt.UTC)
    async with disposable_async_session() as session:
        recipient_ids = await ListDueWeeklyControversyRecipientIdsService.build(session).execute(
            now=now,
        )

    for recipient_id in recipient_ids:
        try:
            await run_weekly_controversy_digest_for_recipient_safe(
                recipient_user_id=recipient_id,
            )
        except Exception:
            logger.exception(
                'weekly controversy digest batch failed recipient=%s',
                recipient_id,
            )


def register_tasks(app: Celery) -> None:
    @app.task(name='tasks.weekly_controversy.send_weekly_controversy_digests')
    def send_weekly_controversy_digests_task() -> None:
        try:
            _run_async_isolated(_send_weekly_controversy_digests_batch_async())
        except Exception:
            logger.exception('celery task send_weekly_controversy_digests_task failed')
