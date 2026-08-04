from __future__ import annotations

import pytest

from models.film import Film
from services.tmdb.sync_film_from_tmdb import SyncFilmFromTmdbService
from tests.support.fake_tmdb_transport import (
    FakeTmdbTransport,
    fight_club_movie_detail,
)


@pytest.mark.asyncio
async def test_sync_film_from_tmdb_fills_missing_gamification_fields() -> None:
    transport = FakeTmdbTransport(
        find_by_imdb={'tt0137523': 550},
        movies_by_id={550: fight_club_movie_detail()},
    )
    syncer = SyncFilmFromTmdbService.build(transport=transport)
    film = Film(
        kinopoisk_id=999001,
        title='Fight Club',
        year=1999,
        poster_url=None,
        genres=[],
        countries=[],
        imdb_id='tt0137523',
    )

    result = await syncer.execute(None, film)  # type: ignore[arg-type]

    assert result.synced is True
    assert film.tmdb_id == 550
    assert film.primary_director_name == 'David Fincher'
    assert film.primary_director_tmdb_id == 6886
    assert film.franchise_key == 'kp_franchise:999001'
    assert film.countries == ['Соединенные Штаты Америки']
    assert film.tmdb_synced_at is not None


@pytest.mark.asyncio
async def test_sync_does_not_overwrite_kp_director_id_or_kp_franchise() -> None:
    transport = FakeTmdbTransport(
        find_by_imdb={'tt0137523': 550},
        movies_by_id={550: fight_club_movie_detail()},
    )
    syncer = SyncFilmFromTmdbService.build(transport=transport)
    film = Film(
        kinopoisk_id=999002,
        title='Fight Club',
        year=1999,
        poster_url=None,
        genres=[],
        countries=['Россия'],
        primary_director_kinopoisk_id=12345,
        primary_director_name='КП Режиссёр',
        franchise_key='kp_franchise:100',
        imdb_id='tt0137523',
    )

    await syncer.execute(None, film, force_gamification=False)  # type: ignore[arg-type]

    assert film.primary_director_kinopoisk_id == 12345
    assert film.primary_director_name == 'КП Режиссёр'
    assert film.franchise_key == 'kp_franchise:100'
    assert film.tmdb_id == 550


@pytest.mark.asyncio
async def test_sync_uses_title_search_when_imdb_missing() -> None:
    transport = FakeTmdbTransport(
        movies_by_id={550: fight_club_movie_detail()},
        search_results={('Fight Club', 1999): 550},
    )
    syncer = SyncFilmFromTmdbService.build(transport=transport)
    film = Film(
        kinopoisk_id=999003,
        title='Fight Club',
        year=1999,
        poster_url=None,
        genres=[],
        countries=[],
    )
    result = await syncer.execute(None, film)  # type: ignore[arg-type]
    assert result.synced is True
    assert film.tmdb_id == 550


@pytest.mark.asyncio
async def test_sync_not_found_returns_reason() -> None:
    transport = FakeTmdbTransport()
    syncer = SyncFilmFromTmdbService.build(transport=transport)
    film = Film(
        kinopoisk_id=999004,
        title='Unknown Film XYZ',
        year=1900,
        poster_url=None,
        genres=[],
        countries=[],
    )
    result = await syncer.execute(None, film)  # type: ignore[arg-type]
    assert result.synced is False
    assert result.reason == 'tmdb movie not found'


@pytest.mark.asyncio
async def test_sync_fills_overview_when_descriptions_missing() -> None:
    transport = FakeTmdbTransport(
        find_by_imdb={'tt0137523': 550},
        movies_by_id={550: fight_club_movie_detail()},
    )
    syncer = SyncFilmFromTmdbService.build(transport=transport)
    film = Film(
        kinopoisk_id=999005,
        title='Fight Club',
        year=1999,
        poster_url=None,
        genres=[],
        countries=[],
        imdb_id='tt0137523',
    )
    await syncer.execute(None, film)  # type: ignore[arg-type]
    assert film.short_description is not None
    assert film.description is not None
