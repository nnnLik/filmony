"""Celery application: broker Redis, workers (no beat)."""

from __future__ import annotations

import gc

from celery import Celery
from celery.signals import worker_before_create_process

from conf import settings

app = Celery('filmony')
app.conf.update(
    broker_url=settings.celery.broker_url,
    result_backend=settings.celery.result_backend,
    broker_connection_retry_on_startup=True,
    task_ignore_result=settings.celery.result_backend is None,
)


@worker_before_create_process.connect
def freeze_gc_before_worker_fork(
    **_: dict,
) -> None:
    """
    Freeze all current tracked objects and ignore them for future collections.
    This can be used before a POSIX fork() call to make the gc copy-on-write friendly.
    Explanation: https://www.youtube.com/watch?v=Hgw_RlCaIds
    """
    gc.collect()
    gc.freeze()


def _register_all_tasks(application: Celery) -> None:
    from tasks.ping import register_tasks as register_ping_tasks
    from tasks.telegram_engagement import register_tasks as register_telegram_engagement_tasks

    register_ping_tasks(application)
    register_telegram_engagement_tasks(application)


_register_all_tasks(app)
