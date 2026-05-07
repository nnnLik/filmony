"""Registered Celery tasks include ping smoke and telegram engagement helpers."""

from __future__ import annotations

import celery_app


def test_celery_app_registers_ping_task() -> None:
    assert 'tasks.ping' in celery_app.app.tasks


def test_celery_app_registers_telegram_engagement_tasks() -> None:
    assert 'tasks.telegram_engagement.notify_comment_reply' in celery_app.app.tasks
    assert 'tasks.telegram_engagement.notify_movie_card_root_comment' in celery_app.app.tasks
    assert 'tasks.telegram_engagement.notify_reaction_added' in celery_app.app.tasks
    assert 'tasks.telegram_engagement.deliver_shared_movie_card' in celery_app.app.tasks
