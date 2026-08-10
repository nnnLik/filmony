"""Integration tests for watch party v2 maintenance and bridge."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest
import sqlalchemy as sa
from httpx import AsyncClient
from sqlalchemy import update

from conf import settings
from core.database import get_session_factory
from models.film import Film
from models.user import User
from models.watch_party import WatchParty, WatchPartyWatchSessionLink
from models.watch_session import WatchSession
from services.films.resolve_film_playback import FilmPlaybackDTO, ResolveFilmPlaybackService
from services.watch_parties.end_expired_watch_parties import EndExpiredWatchPartiesService
from services.watch_parties.watch_party_redis import reset_watch_party_redis_for_tests
from tests.auth.telegram_init_data import build_init_data
from tests.integration.api.test_watch_party_routes import (
    _create_film,
    _create_user,
    _login,
    _patch_playback,
)


@pytest.fixture(autouse=True)
def _reset_redis() -> None:
    reset_watch_party_redis_for_tests()


async def _create_party(async_client: AsyncClient, host: User, film: Film) -> str:
    await _login(async_client, host.telegram_user_id)
    response = await async_client.post('/api/watch-parties', json={'film_id': film.id})
    assert response.status_code == 201
    return response.json()['id']


@pytest.mark.asyncio
async def test_end_expired_watch_parties(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host = await _create_user(telegram_user_id=922001, slug='wp-expire-host')
    film = await _create_film(kinopoisk_id=260001, title='Expire Film')
    _patch_playback(monkeypatch, film)
    party_id = await _create_party(async_client, host, film)

    session_factory = get_session_factory()
    expired_at = (
        datetime.now(tz=UTC) - timedelta(hours=settings.watch_party.ttl_hours + 1)
    ).replace(
        tzinfo=None,
    )
    async with session_factory() as session:
        await session.execute(
            update(WatchParty).where(WatchParty.id == UUID(party_id)).values(created_at=expired_at),
        )
        await session.commit()

    async with session_factory() as session:
        ended = await EndExpiredWatchPartiesService.build(session).execute()
        assert ended == 1

    gone = await async_client.get(f'/api/watch-parties/{party_id}')
    assert gone.status_code == 404


@pytest.mark.asyncio
async def test_batch_watching_after_heartbeat(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host = await _create_user(telegram_user_id=922002, slug='wp-watch-host')
    film = await _create_film(kinopoisk_id=260002, title='Watching Film')
    _patch_playback(monkeypatch, film)
    party_id = await _create_party(async_client, host, film)

    heartbeat = await async_client.post(f'/api/watch-parties/{party_id}/heartbeat')
    assert heartbeat.status_code == 204

    batch = await async_client.post(
        '/api/watch-parties/watching/batch',
        json={'user_ids': [str(host.id)]},
    )
    assert batch.status_code == 200
    items = batch.json()['items']
    assert str(host.id) in items
    assert items[str(host.id)]['film_id'] == film.id


@pytest.mark.asyncio
async def test_bridge_watch_party_to_watch_session(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host = await _create_user(telegram_user_id=922003, slug='wp-bridge-host')
    guest = await _create_user(telegram_user_id=922004, slug='wp-bridge-guest')
    film = await _create_film(kinopoisk_id=260003, title='Bridge Film')
    _patch_playback(monkeypatch, film)
    party_id = await _create_party(async_client, host, film)

    await _login(async_client, guest.telegram_user_id)
    joined = await async_client.post(f'/api/watch-parties/{party_id}/join')
    assert joined.status_code == 204

    await _login(async_client, host.telegram_user_id)
    bridged = await async_client.post(f'/api/watch-parties/{party_id}/bridge-watch-session')
    assert bridged.status_code == 200
    watch_session_id = bridged.json()['watch_session_id']

    session_factory = get_session_factory()
    async with session_factory() as session:
        watch_session = await session.get(WatchSession, UUID(watch_session_id))
        assert watch_session is not None
        assert watch_session.anchor_film_id == film.id
        link = (
            await session.execute(
                sa.select(WatchPartyWatchSessionLink).where(
                    WatchPartyWatchSessionLink.watch_session_id == UUID(watch_session_id),
                ),
            )
        ).scalar_one()
        assert link.watch_party_id == UUID(party_id)
        assert str(host.id) in watch_session.participant_user_ids
        assert str(guest.id) in watch_session.participant_user_ids
