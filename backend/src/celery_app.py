"""Celery application: broker Redis, workers (no beat)."""

from __future__ import annotations

from celery import Celery

from conf import settings

app = Celery('filmony')
app.conf.update(
    broker_url=settings.celery.broker_url,
    result_backend=settings.celery.result_backend,
    broker_connection_retry_on_startup=True,
    task_ignore_result=settings.celery.result_backend is None,
)


def _register_all_tasks(application: Celery) -> None:
    from tasks.ping import register_tasks as register_ping_tasks
    from tasks.telegram_engagement import register_tasks as register_telegram_engagement_tasks

    register_ping_tasks(application)
    register_telegram_engagement_tasks(application)


_register_all_tasks(app)
