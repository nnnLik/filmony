"""Celery tasks: co-view watch session finalize."""

from __future__ import annotations

import asyncio
import concurrent.futures
import logging
from uuid import UUID

from celery import Celery

from core.database import disposable_async_session
from services.watch_sessions.finalize_watch_session_if_ready import (
    FinalizeWatchSessionIfReadyService,
)

logger = logging.getLogger(__name__)


def _run_async_isolated(coro) -> None:
    def _runner() -> None:
        asyncio.run(coro)

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        fut = pool.submit(_runner)
        fut.result(timeout=120)


async def _finalize_watch_session_if_ready_async(watch_session_id: UUID) -> None:
    async with disposable_async_session() as session:
        await FinalizeWatchSessionIfReadyService.build(session).execute(
            watch_session_id=watch_session_id,
        )


def register_tasks(app: Celery) -> None:
    @app.task(name='tasks.watch_session.finalize_watch_session_if_ready')
    def finalize_watch_session_if_ready_task(watch_session_id: str) -> None:
        try:
            _run_async_isolated(
                _finalize_watch_session_if_ready_async(UUID(watch_session_id)),
            )
        except Exception:
            logger.exception(
                'celery task finalize_watch_session_if_ready_task failed session=%s',
                watch_session_id,
            )
