"""Celery tasks: personal weekly and monthly Telegram digests.

Beat schedule (host crontab on prod — see docs/engineering/prod-cron-filmony.md):

    send_weekly_personal_digests:  Monday 10:00 UTC
    send_monthly_personal_digests:  1st day 10:00 UTC

Implementation: docs/superpowers/specs/2026-08-08-personal-digest-redesign-design.md
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import datetime as dt
import logging

from celery import Celery

from services.personal_digest.send_personal_digest_telegram import (
    run_monthly_personal_digest_for_recipient_safe,
    run_weekly_personal_digest_for_recipient_safe,
)
from services.personal_digest.week_bounds import previous_complete_iso_week
from services.profile.build_monthly_recap import previous_complete_month

logger = logging.getLogger(__name__)


def _run_async_isolated(coro) -> None:
    def _runner() -> None:
        asyncio.run(coro)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(_runner)
        fut.result(timeout=300)


async def _send_weekly_personal_digests_batch_async() -> None:
    from core.database import disposable_async_session
    from services.personal_digest.list_due_personal_digest_recipients import (
        ListDuePersonalDigestRecipientIdsService,
    )

    period_key, _, _ = previous_complete_iso_week()
    async with disposable_async_session() as session:
        recipient_ids = await ListDuePersonalDigestRecipientIdsService.build(session).execute(
            period='week',
            period_key=period_key,
        )

    for recipient_id in recipient_ids:
        try:
            await run_weekly_personal_digest_for_recipient_safe(
                recipient_user_id=recipient_id,
                period_key=period_key,
            )
        except Exception:
            logger.exception(
                'weekly personal digest batch failed recipient=%s',
                recipient_id,
            )


async def _send_monthly_personal_digests_batch_async() -> None:
    from core.database import disposable_async_session
    from services.personal_digest.list_due_personal_digest_recipients import (
        ListDuePersonalDigestRecipientIdsService,
    )

    now = dt.datetime.now(tz=dt.UTC)
    year, month = previous_complete_month(now=now)
    async with disposable_async_session() as session:
        recipient_ids = await ListDuePersonalDigestRecipientIdsService.build(session).execute(
            period='month',
            year=year,
            month=month,
        )

    for recipient_id in recipient_ids:
        try:
            await run_monthly_personal_digest_for_recipient_safe(
                recipient_user_id=recipient_id,
                year=year,
                month=month,
            )
        except Exception:
            logger.exception(
                'monthly personal digest batch failed recipient=%s',
                recipient_id,
            )


def register_tasks(app: Celery) -> None:
    @app.task(name='tasks.personal_digest.send_weekly_personal_digests')
    def send_weekly_personal_digests_task() -> None:
        try:
            _run_async_isolated(_send_weekly_personal_digests_batch_async())
        except Exception:
            logger.exception('celery task send_weekly_personal_digests_task failed')

    @app.task(name='tasks.personal_digest.send_monthly_personal_digests')
    def send_monthly_personal_digests_task() -> None:
        try:
            _run_async_isolated(_send_monthly_personal_digests_batch_async())
        except Exception:
            logger.exception('celery task send_monthly_personal_digests_task failed')
