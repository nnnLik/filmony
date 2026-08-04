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

    with patch('services.kinopoisk.resolve_kinopoisk_film.KinopoiskClient') as mock_client_cls:
        mock_client_cls.return_value.get_film = AsyncMock(return_value=payload)
        service = ResolveKinopoiskFilmService(session)
        service._tmdb_sync = mock_tmdb
        film = await service.execute('https://www.kinopoisk.ru/film/301/')

    assert film.imdb_id == 'tt0133093'
    assert film.kinopoisk_id == 301
    mock_tmdb.execute.assert_awaited_once()
