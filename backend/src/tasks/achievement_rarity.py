"""Celery tasks: recalculate achievement rarity snapshots.

Beat schedule (document only — configure externally):
    recalculate_achievement_rarity: daily 03:00 UTC (crontab minute=0 hour=3)
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


async def _recalculate_achievement_rarity_async() -> None:
    from core.database import disposable_async_session
    from services.achievements.recalculate_achievement_rarity import (
        RecalculateAchievementRarityService,
    )

    async with disposable_async_session() as session:
        await RecalculateAchievementRarityService.build(session).execute(achievement_id=None)


def register_tasks(app: Celery) -> None:
    @app.task(name='tasks.achievement_rarity.recalculate_achievement_rarity')
    def recalculate_achievement_rarity_task() -> None:
        try:
            _run_async_isolated(_recalculate_achievement_rarity_async())
        except Exception:
            logger.exception('celery task recalculate_achievement_rarity_task failed')
