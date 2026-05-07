"""Engagement Telegram notifications: reply + reaction add (Celery eager in tests)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import celery_app
import pytest
from httpx import AsyncClient

from tests.api.test_reactions_routes import (
    _create_card_any,
    _login,
    _seed_reaction_catalog,
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


@pytest.mark.asyncio
async def test_comment_reply_triggers_telegram_dm(async_client: AsyncClient) -> None:
    await _seed_reaction_catalog()
    with patch(
        'services.telegram.engagement_delivery.deliver_engagement_html_message',
        new_callable=AsyncMock,
    ) as mock_dm:
        mock_dm.return_value = None
        cid = await _create_card_any(async_client, tg=860_101, kid=860_101)
        root = await async_client.post(
            f'/api/cards/{cid}/comments',
            json={'text': 'root'},
        )
        assert root.status_code == 200
        com_id = root.json()['id']

        await _login(async_client, telegram_user_id=860_102)
        reply = await async_client.post(
            f'/api/cards/{cid}/comments',
            json={'text': 'child', 'parent_comment_id': com_id},
        )
        assert reply.status_code == 200

        mock_dm.assert_awaited_once()
        args, _kwargs = mock_dm.await_args
        assert args[0] == 860_101
        assert 'Filmony' in args[1] and '💬' in args[1]


@pytest.mark.asyncio
async def test_comment_reply_skips_self_reply(async_client: AsyncClient) -> None:
    await _seed_reaction_catalog()
    with patch(
        'services.telegram.engagement_delivery.deliver_engagement_html_message',
        new_callable=AsyncMock,
    ) as mock_dm:
        mock_dm.return_value = None
        cid = await _create_card_any(async_client, tg=860_201, kid=860_201)
        root = await async_client.post(
            f'/api/cards/{cid}/comments',
            json={'text': 'solo'},
        )
        com_id = root.json()['id']
        same = await async_client.post(
            f'/api/cards/{cid}/comments',
            json={'text': 'to self', 'parent_comment_id': com_id},
        )
        assert same.status_code == 200

        mock_dm.assert_not_awaited()


@pytest.mark.asyncio
async def test_reaction_added_triggers_dm_once(async_client: AsyncClient) -> None:
    rx1, *_rest = await _seed_reaction_catalog()
    with patch(
        'services.telegram.engagement_delivery.deliver_engagement_html_message',
        new_callable=AsyncMock,
    ) as mock_dm:
        mock_dm.return_value = None
        cid = await _create_card_any(async_client, tg=860_301, kid=860_301)
        await _login(async_client, telegram_user_id=860_302)
        first = await async_client.post(
            '/api/reactions',
            json={
                'target_kind': 'movie_card',
                'target_id': cid,
                'reaction_type_id': rx1,
            },
        )
        assert first.status_code == 200
        second = await async_client.post(
            '/api/reactions',
            json={
                'target_kind': 'movie_card',
                'target_id': cid,
                'reaction_type_id': rx1,
            },
        )
        assert second.status_code == 200

        mock_dm.assert_awaited_once()
        args, _kwargs = mock_dm.await_args
        assert args[0] == 860_301
        assert 'Реакция' in args[1] and '👤' in args[1]
