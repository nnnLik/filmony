"""Celery tasks: watch party maintenance."""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging

from celery import Celery

from core.database import disposable_async_session
from services.watch_parties.end_expired_watch_parties import EndExpiredWatchPartiesService

logger = logging.getLogger(__name__)


def _run_async_isolated(coro) -> int:
    def _runner() -> int:
        return asyncio.run(coro)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(_runner)
        return int(fut.result(timeout=120))


async def _end_expired_watch_parties_async() -> int:
    async with disposable_async_session() as session:
        return await EndExpiredWatchPartiesService.build(session).execute()


def register_tasks(app: Celery) -> None:
    @app.task(name='tasks.watch_party.end_expired_watch_parties')
    def end_expired_watch_parties_task() -> int:
        try:
            return _run_async_isolated(_end_expired_watch_parties_async())
        except Exception:
            logger.exception('celery task end_expired_watch_parties_task failed')
            raise
