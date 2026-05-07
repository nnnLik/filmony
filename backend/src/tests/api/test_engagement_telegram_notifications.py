"""Engagement Telegram notifications: reply + reaction add (Celery eager in tests)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

import celery_app
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
        assert 'Новый ответ' in args[1] and 'Открыть в Filmony' in args[1]


@pytest.mark.asyncio
async def test_root_comment_on_card_notifies_owner(async_client: AsyncClient) -> None:
    await _seed_reaction_catalog()
    with patch(
        'services.telegram.engagement_delivery.deliver_engagement_html_message',
        new_callable=AsyncMock,
    ) as mock_dm:
        mock_dm.return_value = None
        cid = await _create_card_any(async_client, tg=860_801, kid=860_801)
        await _login(async_client, telegram_user_id=860_802)
        r = await async_client.post(
            f'/api/cards/{cid}/comments',
            json={'text': 'первый комментарий под карточкой'},
        )
        assert r.status_code == 200
        mock_dm.assert_awaited_once()
        args, _kwargs = mock_dm.await_args
        assert args[0] == 860_801
        assert 'Новый комментарий' in args[1] and 'Открыть в Filmony' in args[1]


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
        body = args[1]
        assert 'отреагировал' in body and 'Открыть в Filmony' in body
        assert 'Rf 860301' in body


@pytest.mark.asyncio
async def test_two_users_same_reaction_type_both_trigger_dm(async_client: AsyncClient) -> None:
    """Вторая персона ставит тот же тип реакции, что уже есть у другого — всё равно «добавление», нужен отдельный DM."""
    rx1, *_rest = await _seed_reaction_catalog()
    with patch(
        'services.telegram.engagement_delivery.deliver_engagement_html_message',
        new_callable=AsyncMock,
    ) as mock_dm:
        mock_dm.return_value = None
        cid = await _create_card_any(async_client, tg=860_601, kid=860_601)

        await _login(async_client, telegram_user_id=860_602)
        first = await async_client.post(
            '/api/reactions',
            json={
                'target_kind': 'movie_card',
                'target_id': cid,
                'reaction_type_id': rx1,
            },
        )
        assert first.status_code == 200

        await _login(async_client, telegram_user_id=860_603)
        second = await async_client.post(
            '/api/reactions',
            json={
                'target_kind': 'movie_card',
                'target_id': cid,
                'reaction_type_id': rx1,
            },
        )
        assert second.status_code == 200

        assert mock_dm.await_count == 2
        for call in mock_dm.await_args_list:
            assert call.args[0] == 860_601
        bodies = [c.args[1] for c in mock_dm.await_args_list]
        assert all(
            'отреагировал' in b and 'Открыть в Filmony' in b and 'Rf 860601' in b for b in bodies
        )


@pytest.mark.asyncio
async def test_reaction_on_comment_triggers_dm(async_client: AsyncClient) -> None:
    rx1, *_rest = await _seed_reaction_catalog()
    with patch(
        'services.telegram.engagement_delivery.deliver_engagement_html_message',
        new_callable=AsyncMock,
    ) as mock_dm:
        mock_dm.return_value = None
        cid = await _create_card_any(async_client, tg=860_401, kid=860_401)
        cm = await async_client.post(f'/api/cards/{cid}/comments', json={'text': 'root'})
        assert cm.status_code == 200
        com_id = cm.json()['id']

        await _login(async_client, telegram_user_id=860_402)
        rr = await async_client.post(
            '/api/reactions',
            json={
                'target_kind': 'movie_card_comment',
                'target_id': com_id,
                'reaction_type_id': rx1,
            },
        )
        assert rr.status_code == 200

        mock_dm.assert_awaited_once()
        args, _kwargs = mock_dm.await_args
        assert args[0] == 860_401
        body = args[1]
        assert 'Реакция на ваш комментарий' in body and 'Открыть в Filmony' in body
        assert 'root' in body
