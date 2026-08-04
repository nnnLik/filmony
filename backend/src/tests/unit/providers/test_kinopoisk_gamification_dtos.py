from __future__ import annotations

import pytest

from providers.kinopoisk.kinopoisk_sequels_dto import (
    KinopoiskSequelFilmDTO,
    sequel_films_from_list,
)
from providers.kinopoisk.kinopoisk_staff_dto import (
    KinopoiskStaffMemberDTO,
    staff_members_from_list,
)


def test_kinopoisk_staff_member_dto_from_dict() -> None:
    dto = KinopoiskStaffMemberDTO.from_dict(
        {
            'staffId': 1001,
            'nameRu': 'Кристофер Нолан',
            'nameEn': 'Christopher Nolan',
            'professionKey': 'DIRECTOR',
            'posterUrl': 'https://kinopoisk-ru.clstorage.net/staff/1001.jpg',
        },
    )
    assert dto.staff_id == 1001
    assert dto.display_name() == 'Кристофер Нолан'
    assert dto.profession_key == 'DIRECTOR'
    assert dto.poster_url == 'https://kinopoisk-ru.clstorage.net/staff/1001.jpg'


def test_staff_members_from_list_skips_invalid_rows() -> None:
    members = staff_members_from_list(
        [
            {'staffId': 1, 'nameRu': 'A', 'professionKey': 'ACTOR'},
            {'staffId': 'bad'},
            {'staffId': 2, 'nameEn': 'Director', 'professionKey': 'DIRECTOR'},
        ],
    )
    assert len(members) == 2
    assert members[1].staff_id == 2


def test_kinopoisk_sequel_film_dto_from_dict() -> None:
    dto = KinopoiskSequelFilmDTO.from_dict(
        {
            'filmId': 301,
            'nameRu': 'Матрица: Перезагрузка',
            'relationType': 'SEQUEL',
        },
    )
    assert dto.film_id == 301
    assert dto.relation_type == 'SEQUEL'


def test_sequel_films_from_list_skips_invalid_rows() -> None:
    sequels = sequel_films_from_list(
        [
            {'filmId': 301, 'nameRu': 'Sequel', 'relationType': 'SEQUEL'},
            {'filmId': 'bad'},
        ],
    )
    assert len(sequels) == 1
    assert sequels[0].film_id == 301
