"""Celery batch task for subscribed-activity Telegram digest."""

from __future__ import annotations

from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

import celery_app
from services.telegram.send_subscribed_activity_digest import (
    DigestDeliveryOutcome,
    DigestDeliveryResult,
)


@pytest.fixture(autouse=True)
def _celery_always_eager() -> None:
    app = celery_app.app
    prev_eager = app.conf.task_always_eager
    prev_prop = app.conf.task_eager_propagates
    app.conf.task_always_eager = True
    app.conf.task_eager_propagates = True
    yield
    app.conf.task_always_eager = prev_eager
    app.conf.task_eager_propagates = prev_prop


def test_celery_registers_subscribed_activity_digest_task() -> None:
    assert 'tasks.telegram_engagement.send_subscribed_activity_digests' in celery_app.app.tasks


@pytest.mark.asyncio
async def test_batch_task_processes_due_recipients() -> None:
    rid = uuid4()
    mock_due = AsyncMock(return_value=[rid])
    mock_send = AsyncMock(
        return_value=DigestDeliveryResult(
            outcome=DigestDeliveryOutcome.sent,
            recipient_user_id=rid,
        )
    )
    mock_session = AsyncMock()

    @asynccontextmanager
    async def _fake_disposable_session():
        yield mock_session

    with (
        patch(
            'services.telegram.list_due_subscribed_activity_digest_recipients'
            '.ListDueSubscribedActivityDigestRecipientIdsService',
        ) as mock_list_cls,
        patch(
            'tasks.telegram_engagement.run_subscribed_activity_digest_for_recipient_safe',
            mock_send,
        ),
        patch(
            'core.database.disposable_async_session',
            _fake_disposable_session,
        ),
    ):
        mock_list_cls.build.return_value.execute = mock_due
        celery_app.app.tasks['tasks.telegram_engagement.send_subscribed_activity_digests'].apply()

    mock_send.assert_awaited_once_with(recipient_user_id=rid)


@pytest.mark.asyncio
async def test_batch_task_isolates_recipient_failures() -> None:
    rid1, rid2 = uuid4(), uuid4()
    mock_due = AsyncMock(return_value=[rid1, rid2])
    mock_session = AsyncMock()

    @asynccontextmanager
    async def _fake_disposable_session():
        yield mock_session

    async def _side_effect(*, recipient_user_id):
        if recipient_user_id == rid1:
            raise RuntimeError('boom')
        return DigestDeliveryResult(
            outcome=DigestDeliveryOutcome.sent,
            recipient_user_id=recipient_user_id,
        )

    mock_send = AsyncMock(side_effect=_side_effect)

    with (
        patch(
            'services.telegram.list_due_subscribed_activity_digest_recipients'
            '.ListDueSubscribedActivityDigestRecipientIdsService',
        ) as mock_list_cls,
        patch(
            'tasks.telegram_engagement.run_subscribed_activity_digest_for_recipient_safe',
            mock_send,
        ),
        patch(
            'core.database.disposable_async_session',
            _fake_disposable_session,
        ),
    ):
        mock_list_cls.build.return_value.execute = mock_due
        celery_app.app.tasks['tasks.telegram_engagement.send_subscribed_activity_digests'].apply()

    assert mock_send.await_count == 2
