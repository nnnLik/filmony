"""GET /api/films/{film_id}/playback — pleer.video embed resolver."""

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


async def _create_user(*, telegram_user_id: int) -> User:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            telegram_user_id=telegram_user_id,
            profile_slug=f'playback-{telegram_user_id}',
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
        expires_at=datetime.now(tz=UTC) + timedelta(minutes=10),
    )


@pytest.mark.asyncio
async def test_get_film_playback_returns_iframe_url(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = await _create_user(telegram_user_id=910001)
    film = await _create_film(kinopoisk_id=258687, title='Интерстеллар')
    dto = _playback_dto(film)

    class FakeService:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        async def execute(self, film_id: int, _viewer_user_id) -> FilmPlaybackDTO:
            assert film_id == film.id
            return dto

    def _fake_build(_cls, _session):
        return FakeService()

    monkeypatch.setattr(
        ResolveFilmPlaybackService,
        'build',
        classmethod(_fake_build),
    )

    await _login(async_client, user.telegram_user_id)
    response = await async_client.get(f'/api/films/{film.id}/playback')
    assert response.status_code == 200
    body = response.json()
    assert body['provider'] == 'pleer.video'
    assert body['iframe_url'] == f'https://pleer.video/{film.kinopoisk_id}'
    assert body['film_id'] == film.id
    assert body['kinopoisk_id'] == film.kinopoisk_id


@pytest.mark.asyncio
async def test_get_film_playback_film_not_found(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=910002)
    await _login(async_client, user.telegram_user_id)
    response = await async_client.get('/api/films/999999999/playback')
    assert response.status_code == 404
    assert response.json()['detail'] == 'film_not_found'


@pytest.mark.asyncio
async def test_get_film_playback_unavailable(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    user = await _create_user(telegram_user_id=910003)
    film = await _create_film(kinopoisk_id=777777, title='Missing film')

    class FakeService:
        def __init__(self, *_args, **_kwargs) -> None:
            pass

        async def execute(self, film_id: int, _viewer_user_id) -> FilmPlaybackDTO:
            assert film_id == film.id
            raise ResolveFilmPlaybackService.PlaybackUnavailable

    def _fake_build(_cls, _session):
        return FakeService()

    monkeypatch.setattr(
        ResolveFilmPlaybackService,
        'build',
        classmethod(_fake_build),
    )

    await _login(async_client, user.telegram_user_id)
    response = await async_client.get(f'/api/films/{film.id}/playback')
    assert response.status_code == 422
    assert response.json()['detail'] == 'playback_unavailable'


@pytest.mark.asyncio
async def test_get_film_playback_requires_auth(async_client: AsyncClient) -> None:
    response = await async_client.get('/api/films/1/playback')
    assert response.status_code == 401
