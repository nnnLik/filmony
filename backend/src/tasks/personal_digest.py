"""Celery tasks: personal weekly and monthly Telegram digests.

Beat schedule (host crontab on prod — see docs/engineering/prod-cron-filmony.md):

    send_weekly_personal_digests:  Monday 10:00 UTC
    send_monthly_personal_digests:  1st day 10:00 UTC

Implementation: docs/superpowers/specs/2026-08-08-personal-digest-redesign-design.md
Phase 0 registers tasks + batch entrypoints; full BuildPersonalDigestService in Phase 1–2.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging

from celery import Celery

logger = logging.getLogger(__name__)

_SPEC = 'docs/superpowers/specs/2026-08-08-personal-digest-redesign-design.md'


def _run_async_isolated(coro) -> None:
    def _runner() -> None:
        asyncio.run(coro)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(_runner)
        fut.result(timeout=300)


async def _send_weekly_personal_digests_batch_async() -> None:
    logger.info(
        'personal_digest weekly batch: stub (Phase 1–2 pending) — see %s',
        _SPEC,
    )


async def _send_monthly_personal_digests_batch_async() -> None:
    logger.info(
        'personal_digest monthly batch: stub (Phase 1 pending) — see %s',
        _SPEC,
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
