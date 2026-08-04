"""Celery task registration for monthly recap nudges."""

from __future__ import annotations

import celery_app


def test_celery_registers_monthly_recap_nudge_task() -> None:
    assert 'tasks.monthly_recap.send_monthly_recap_nudges' in celery_app.app.tasks
