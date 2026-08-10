"""Watch party REST routes — create/join/get/end/kick."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from conf import settings
from core.database import get_session_factory
from models.film import Film
from models.user import User
from services.films.resolve_film_playback import FilmPlaybackDTO, ResolveFilmPlaybackService
from tests.auth.telegram_init_data import build_init_data


async def _login(async_client: AsyncClient, telegram_user_id: int) -> None:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    response = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert response.status_code == 200


async def _create_user(*, telegram_user_id: int, slug: str) -> User:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            telegram_user_id=telegram_user_id,
            profile_slug=slug,
            display_name=f'User {telegram_user_id}',
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def _create_film(*, kinopoisk_id: int, title: str) -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title=title,
            year=2014,
            poster_url='https://example.com/poster.jpg',
            genres=['фантастика'],
        )
        session.add(film)
        await session.commit()
        await session.refresh(film)
        return film


def _playback_dto(film: Film) -> FilmPlaybackDTO:
    return FilmPlaybackDTO(
        provider='pleer.video',
        title=film.title,
        iframe_url=f'https://pleer.video/{film.kinopoisk_id}',
        film_id=film.id,
        kinopoisk_id=film.kinopoisk_id,
        expires_at=datetime.now(tz=UTC) + timedelta(hours=1),
    )


def _patch_playback(monkeypatch: pytest.MonkeyPatch, film: Film) -> None:
    dto = _playback_dto(film)

    class FakeService:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        async def execute(self, film_id: int, _viewer_user_id) -> FilmPlaybackDTO:
            assert film_id == film.id
            return dto

    monkeypatch.setattr(
        ResolveFilmPlaybackService,
        'build',
        classmethod(lambda _cls, _session: FakeService()),
    )


@pytest.mark.asyncio
async def test_create_watch_party_success(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host = await _create_user(telegram_user_id=920001, slug='wp-host-1')
    film = await _create_film(kinopoisk_id=258687, title='Интерстеллар')
    _patch_playback(monkeypatch, film)

    await _login(async_client, host.telegram_user_id)
    response = await async_client.post('/api/watch-parties', json={'film_id': film.id})
    assert response.status_code == 201
    body = response.json()
    assert body['invite_slug']
    assert body['invite_url'].endswith(f'/watch-party/{body["invite_slug"]}')

    snapshot = await async_client.get(f'/api/watch-parties/{body["id"]}')
    assert snapshot.status_code == 200
    snap = snapshot.json()
    assert snap['film_id'] == film.id
    assert snap['viewer_role'] == 'host'
    assert len(snap['members']) == 1


@pytest.mark.asyncio
async def test_create_watch_party_playback_unavailable(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host = await _create_user(telegram_user_id=920002, slug='wp-host-2')
    film = await _create_film(kinopoisk_id=777001, title='No playback')

    class FakeService:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        async def execute(self, _film_id: int, _viewer_user_id) -> FilmPlaybackDTO:
            raise ResolveFilmPlaybackService.PlaybackUnavailable

    monkeypatch.setattr(
        ResolveFilmPlaybackService,
        'build',
        classmethod(lambda _cls, _session: FakeService()),
    )

    await _login(async_client, host.telegram_user_id)
    response = await async_client.post('/api/watch-parties', json={'film_id': film.id})
    assert response.status_code == 422
    assert response.json()['detail'] == 'playback_unavailable'


@pytest.mark.asyncio
async def test_join_watch_party_and_conflict(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host = await _create_user(telegram_user_id=920003, slug='wp-host-3')
    guest = await _create_user(telegram_user_id=920004, slug='wp-guest-3')
    film = await _create_film(kinopoisk_id=258688, title='Дюна')
    _patch_playback(monkeypatch, film)

    await _login(async_client, host.telegram_user_id)
    created = await async_client.post('/api/watch-parties', json={'film_id': film.id})
    party_id = created.json()['id']

    await _login(async_client, guest.telegram_user_id)
    joined = await async_client.post(f'/api/watch-parties/{party_id}/join')
    assert joined.status_code == 204

    snapshot = await async_client.get(f'/api/watch-parties/{party_id}')
    assert snapshot.status_code == 200
    assert snapshot.json()['viewer_role'] == 'guest'
    assert len(snapshot.json()['members']) == 2

    other_film = await _create_film(kinopoisk_id=258689, title='Other')
    _patch_playback(monkeypatch, other_film)
    conflict = await async_client.post('/api/watch-parties', json={'film_id': other_film.id})
    assert conflict.status_code == 409
    detail = conflict.json()['detail']
    assert detail['code'] == 'already_in_active_party'


@pytest.mark.asyncio
async def test_get_watch_party_by_slug(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host = await _create_user(telegram_user_id=920005, slug='wp-host-5')
    film = await _create_film(kinopoisk_id=258690, title='Бегущий')
    _patch_playback(monkeypatch, film)

    await _login(async_client, host.telegram_user_id)
    created = await async_client.post('/api/watch-parties', json={'film_id': film.id})
    slug = created.json()['invite_slug']

    resolved = await async_client.get(f'/api/watch-parties/by-slug/{slug}')
    assert resolved.status_code == 200
    assert resolved.json()['party_id'] == created.json()['id']


@pytest.mark.asyncio
async def test_end_watch_party_host_only(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host = await _create_user(telegram_user_id=920006, slug='wp-host-6')
    guest = await _create_user(telegram_user_id=920007, slug='wp-guest-6')
    film = await _create_film(kinopoisk_id=258691, title='Матрица')
    _patch_playback(monkeypatch, film)

    await _login(async_client, host.telegram_user_id)
    created = await async_client.post('/api/watch-parties', json={'film_id': film.id})
    party_id = created.json()['id']

    await _login(async_client, guest.telegram_user_id)
    await async_client.post(f'/api/watch-parties/{party_id}/join')

    forbidden = await async_client.post(f'/api/watch-parties/{party_id}/end')
    assert forbidden.status_code == 403
    assert forbidden.json()['detail'] == 'host_required'

    await _login(async_client, host.telegram_user_id)
    ended = await async_client.post(f'/api/watch-parties/{party_id}/end')
    assert ended.status_code == 204

    gone = await async_client.get(f'/api/watch-parties/{party_id}')
    assert gone.status_code == 404


@pytest.mark.asyncio
async def test_kick_guest(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    host = await _create_user(telegram_user_id=920008, slug='wp-host-8')
    guest = await _create_user(telegram_user_id=920009, slug='wp-guest-8')
    film = await _create_film(kinopoisk_id=258692, title='Начало')
    _patch_playback(monkeypatch, film)

    await _login(async_client, host.telegram_user_id)
    created = await async_client.post('/api/watch-parties', json={'film_id': film.id})
    party_id = created.json()['id']

    await _login(async_client, guest.telegram_user_id)
    await async_client.post(f'/api/watch-parties/{party_id}/join')

    await _login(async_client, host.telegram_user_id)
    kicked = await async_client.post(
        f'/api/watch-parties/{party_id}/kick',
        json={'user_id': str(guest.id)},
    )
    assert kicked.status_code == 204

    await _login(async_client, guest.telegram_user_id)
    snapshot = await async_client.get(f'/api/watch-parties/{party_id}')
    assert snapshot.status_code == 403
