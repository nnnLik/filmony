"""Celery tasks: sync Oscar Best Picture badges from curated dataset.

Beat schedule (document only — configure externally):
    sync_film_award_badges: annually after Academy Awards ceremony
        (suggested: minute=0 hour=6 day_of_month=5 month_of_year=3 — first week of March UTC)
    Optional manual/on-demand: send_task after dataset file update any time.
"""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging

from celery import Celery

logger = logging.getLogger(__name__)


def _run_async_isolated(coro) -> None:
    def _runner() -> None:
        asyncio.run(coro)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(_runner)
        fut.result(timeout=300)


async def _sync_film_award_badges_async() -> None:
    from core.database import disposable_async_session
    from services.film_award_badges.sync_film_award_badges import SyncFilmAwardBadgesService

    async with disposable_async_session() as session:
        result = await SyncFilmAwardBadgesService.build(session).execute(dry_run=False)
    logger.info(
        'sync_film_award_badges completed: matched=%d upserted=%d unmatched=%d',
        result.matched,
        result.upserted,
        len(result.unmatched_kinopoisk_ids),
    )


def register_tasks(app: Celery) -> None:
    @app.task(name='tasks.film_award_badges.sync_film_award_badges')
    def sync_film_award_badges_task() -> None:
        try:
            _run_async_isolated(_sync_film_award_badges_async())
        except Exception:
            logger.exception('celery task sync_film_award_badges_task failed')
