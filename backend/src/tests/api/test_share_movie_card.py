"""POST /api/cards/{id}/share — только подписчики автора, очередь Celery."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID

import pytest
from httpx import AsyncClient

from tests.api.test_profile_routes import _login, _seed_movie_card


@pytest.mark.asyncio
async def test_share_movie_card_queues_tasks_for_followers(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    mock_send = MagicMock()
    monkeypatch.setattr('api.cards.routes.celery_application.send_task', mock_send)

    owner = await _login(async_client, telegram_user_id=90101)
    follower = await _login(async_client, telegram_user_id=90102)

    await async_client.post(f'/api/users/{owner["id"]}/subscriptions')

    await _login(async_client, telegram_user_id=90101)

    card_id = await _seed_movie_card(
        user_id=UUID(str(owner['id'])),
        kinopoisk_id=901010,
        title='Share Test Film',
        year=2020,
        rating=8.5,
        company='friends',
        mood_after='enjoyed',
        tags=['инди'],
    )

    res = await async_client.post(
        f'/api/cards/{card_id}/share',
        json={'recipient_user_ids': [follower['id']]},
    )
    assert res.status_code == 200
    assert res.json()['queued'] == 1

    mock_send.assert_called_once()
    args, kw = mock_send.call_args
    assert args[0] == 'tasks.telegram_engagement.deliver_shared_movie_card'
    payload = kw['kwargs']
    assert payload['card_id'] == card_id
    assert payload['actor_user_id'] == str(owner['id'])
    assert payload['recipient_user_id'] == str(follower['id'])


@pytest.mark.asyncio
async def test_share_movie_card_rejects_non_follower(async_client: AsyncClient) -> None:
    owner = await _login(async_client, telegram_user_id=90103)
    stranger = await _login(async_client, telegram_user_id=90104)

    await _login(async_client, telegram_user_id=90103)

    card_id = await _seed_movie_card(
        user_id=UUID(str(owner['id'])),
        kinopoisk_id=901030,
        title='Another Film',
        year=2019,
        rating=7.0,
        company='alone',
        mood_after='tense',
        tags=[],
    )

    res = await async_client.post(
        f'/api/cards/{card_id}/share',
        json={'recipient_user_ids': [stranger['id']]},
    )
    assert res.status_code == 422
