from __future__ import annotations

from providers.tmdb.tmdb_credits_dto import credits_from_dict
from providers.tmdb.tmdb_find_dto import find_response_from_dict, search_response_from_dict
from providers.tmdb.tmdb_mapping import (
    franchise_key_from_movie,
    gamification_preview_from_movie,
    normalize_imdb_id,
)
from providers.tmdb.tmdb_movie_dto import movie_detail_from_dict
from tests.support.fake_tmdb_transport import (
    fight_club_movie_detail,
    star_wars_collection_movie_detail,
)


def test_normalize_imdb_id_adds_tt_prefix() -> None:
    assert normalize_imdb_id('0137523') == 'tt0137523'
    assert normalize_imdb_id('tt0137523') == 'tt0137523'
    assert normalize_imdb_id(None) is None


def test_movie_detail_from_dict_parses_director_and_countries() -> None:
    dto = fight_club_movie_detail()
    preview = gamification_preview_from_movie(dto, kinopoisk_id=301)
    assert preview.primary_director_name == 'David Fincher'
    assert preview.primary_director_tmdb_id == 6886
    assert preview.countries == ['Соединенные Штаты Америки']
    assert preview.franchise_key == 'kp_franchise:301'


def test_franchise_key_uses_tmdb_collection_when_present() -> None:
    dto = star_wars_collection_movie_detail()
    preview = gamification_preview_from_movie(dto, kinopoisk_id=777)
    assert preview.franchise_key == 'tmdb_collection:10'


def test_find_response_from_dict() -> None:
    found = find_response_from_dict(
        {
            'movie_results': [
                {
                    'id': 550,
                    'title': 'Fight Club',
                    'release_date': '1999-10-15',
                },
            ],
        },
    )
    assert found.first_movie_id() == 550


def test_search_response_from_dict() -> None:
    found = search_response_from_dict(
        {
            'results': [
                {
                    'id': 11,
                    'title': 'Star Wars',
                    'release_date': '1977-05-25',
                },
            ],
        },
    )
    assert found.first_movie_id() == 11


def test_credits_from_dict_skips_invalid_crew_rows() -> None:
    credits = credits_from_dict(
        {
            'id': 1,
            'crew': [
                {'id': 1, 'name': 'A', 'job': 'Director', 'department': 'Directing'},
                {'id': 'bad'},
            ],
        },
    )
    assert len(credits.crew) == 1


def test_movie_detail_from_raw_json() -> None:
    dto = movie_detail_from_dict(fight_club_movie_detail().raw)
    assert dto.id == 550
    assert dto.imdb_id == 'tt0137523'


def test_franchise_key_from_movie_helper() -> None:
    assert franchise_key_from_movie(kinopoisk_id=5, collection=None) == 'kp_franchise:5'
