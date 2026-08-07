from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.kinopoisk.client import KinopoiskFilmPayload
from services.kinopoisk.resolve_kinopoisk_film import ResolveKinopoiskFilmService
from services.tmdb.sync_film_from_tmdb import SyncFilmFromTmdbResult


@pytest.mark.asyncio
async def test_resolve_saves_imdb_and_calls_tmdb_sync() -> None:
    payload = KinopoiskFilmPayload(
        kinopoisk_id=301,
        title='Matrix',
        year=1999,
        poster_url='https://example.com/m.jpg',
        genres=['sci-fi'],
        countries=['USA'],
        short_description='Short',
        description='Long',
        imdb_id='tt0133093',
    )
    session = MagicMock()
    session.execute = AsyncMock(return_value=MagicMock(scalar_one_or_none=lambda: None))
    session.add = MagicMock()
    session.flush = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock(side_effect=lambda _obj: None)

    async def capture_sync(_session, film, **kwargs):
        _ = (_session, kwargs)
        return SyncFilmFromTmdbResult(synced=True, tmdb_id=603, imdb_id=film.imdb_id)

    mock_tmdb = MagicMock()
    mock_tmdb.execute = AsyncMock(side_effect=capture_sync)

    mock_transport = MagicMock()
    mock_transport.get_staff_by_film_id = AsyncMock(return_value=())

    with patch('services.kinopoisk.resolve_kinopoisk_film.KinopoiskClient') as mock_client_cls:
        mock_client_cls.return_value.get_film = AsyncMock(return_value=payload)
        service = ResolveKinopoiskFilmService(session)
        service._tmdb_sync = mock_tmdb
        service._kp_transport = mock_transport
        film = await service.execute('https://www.kinopoisk.ru/film/301/')

    assert film.imdb_id == 'tt0133093'
    assert film.kinopoisk_id == 301
    mock_tmdb.execute.assert_awaited_once()


@pytest.mark.asyncio
async def test_sync_metadata_fills_kp_director_when_missing() -> None:
    from models.film import Film
    from providers.kinopoisk.kinopoisk_staff_dto import KinopoiskStaffMemberDTO

    film = Film(
        kinopoisk_id=382,
        title='American History X',
        year=1998,
        poster_url=None,
        genres=[],
        primary_director_name='Тони Кэй',
        primary_director_tmdb_id=814,
        primary_director_kinopoisk_id=None,
    )
    session = MagicMock()
    mock_tmdb = MagicMock()
    mock_tmdb.execute = AsyncMock(
        return_value=SyncFilmFromTmdbResult(synced=True, tmdb_id=73, imdb_id='tt0120586'),
    )
    director = KinopoiskStaffMemberDTO(
        staff_id=66424,
        name_ru='Тони Кэй',
        name_en='Tony Kaye',
        profession_key='DIRECTOR',
        poster_url='https://example.com/tony.jpg',
    )
    mock_transport = MagicMock()
    mock_transport.get_staff_by_film_id = AsyncMock(return_value=(director,))

    service = ResolveKinopoiskFilmService(session)
    service._tmdb_sync = mock_tmdb
    service._kp_transport = mock_transport

    # Autouse test plugin noops sync_metadata_for_film; exercise the real sync path.
    await service._sync_metadata(film)

    assert film.primary_director_kinopoisk_id == 66424
    assert film.primary_director_name == 'Тони Кэй'
    assert film.primary_director_poster_url == 'https://example.com/tony.jpg'
    mock_transport.get_staff_by_film_id.assert_awaited_once_with(382)
