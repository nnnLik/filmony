"""Follower broadcasts on publish: Telegram HTML copy + deep links (Celery eager in tests)."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient

import celery_app
from conf import settings
from tests.api.test_cards_routes import _create_film as _film_cards
from tests.api.test_cards_routes import _login as _login_cards
from tests.api.test_feed_posts_routes import _login as _login_feed


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
async def test_new_card_follower_dm_contains_publish_copy_and_deep_link(
    monkeypatch: pytest.MonkeyPatch,
    async_client: AsyncClient,
) -> None:
    monkeypatch.setattr(settings.telegram, 'bot_username', 'stubfilmony_bot')

    mock_dm = AsyncMock(return_value=None)
    with patch(
        'services.telegram.notify_follower_new_user_card.deliver_engagement_html_message', mock_dm
    ):
        author = await _login_cards(async_client, telegram_user_id=9_771_001)
        await _login_cards(async_client, telegram_user_id=9_771_002)
        await async_client.post(f'/api/users/{author["id"]}/subscriptions')

        await _login_cards(async_client, telegram_user_id=9_771_001)
        film = await _film_cards(kinopoisk_id=977_1001)
        r = await async_client.post(
            '/api/cards',
            json={
                'film_id': film.id,
                'kinopoisk_id': film.kinopoisk_id,
                'genres': [],
                'rating': 8.0,
                'company': 'alone',
                'mood_before': 'relax',
                'mood_after': 'enjoyed',
                'custom_tags': [],
            },
        )
        assert r.status_code == 200
        cid = int(r.json()['id'])

    mock_dm.assert_awaited_once()
    chat_id, html_body = mock_dm.await_args.args
    assert int(chat_id) == 9_771_002
    assert 'опубликовал' in html_body
    assert 'Интерстеллар' in html_body or '«' in html_body
    assert f'startapp=c{cid}' in html_body
    assert 'Открыть в Filmony' in html_body


@pytest.mark.asyncio
async def test_new_feed_post_follower_dm_contains_publish_copy_and_deep_link(
    monkeypatch: pytest.MonkeyPatch,
    async_client: AsyncClient,
) -> None:
    monkeypatch.setattr(settings.telegram, 'bot_username', 'stubfilmony_bot')

    mock_dm = AsyncMock(return_value=None)
    with patch(
        'services.telegram.notify_follower_new_feed_post.deliver_engagement_html_message', mock_dm
    ):
        author = await _login_feed(async_client, telegram_user_id=9_772_001)
        await _login_feed(async_client, telegram_user_id=9_772_002)
        await async_client.post(f'/api/users/{author["id"]}/subscriptions')

        await _login_feed(async_client, telegram_user_id=9_772_001)
        r = await async_client.post(
            '/api/feed-posts',
            json={'body': 'Лента: привет всем подписчикам'},
        )
        assert r.status_code == 200
        post_id = int(r.json()['id'])

    mock_dm.assert_awaited_once()
    chat_id, html_body = mock_dm.await_args.args
    assert int(chat_id) == 9_772_002
    assert 'опубликовал' in html_body and 'пост в ленте' in html_body
    assert 'Лента:' in html_body
    assert f'startapp=p{post_id}' in html_body
    assert 'Открыть пост в ленте' in html_body
