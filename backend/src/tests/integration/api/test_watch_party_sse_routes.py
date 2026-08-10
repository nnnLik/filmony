"""Chat routes for watch parties."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from models.film import Film
from models.user import User
from tests.integration.api.test_watch_party_routes import (
    _create_film,
    _create_user,
    _login,
    _patch_playback,
)


async def _create_party(async_client: AsyncClient, host: User, film: Film) -> str:
    await _login(async_client, host.telegram_user_id)
    response = await async_client.post('/api/watch-parties', json={'film_id': film.id})
    assert response.status_code == 201
    return response.json()['id']


@pytest.mark.asyncio
async def test_create_message_persists(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host = await _create_user(telegram_user_id=921002, slug='wp-chat-host')
    film = await _create_film(kinopoisk_id=259002, title='Chat Film')
    _patch_playback(monkeypatch, film)
    party_id = await _create_party(async_client, host, film)

    created = await async_client.post(
        f'/api/watch-parties/{party_id}/messages',
        json={'body': 'Привет, комната!'},
    )
    assert created.status_code == 201
    assert created.json()['body'] == 'Привет, комната!'

    listed = await async_client.get(f'/api/watch-parties/{party_id}/messages')
    assert listed.status_code == 200
    assert len(listed.json()) == 1
