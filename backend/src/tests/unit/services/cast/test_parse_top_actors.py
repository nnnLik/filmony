from __future__ import annotations

from providers.kinopoisk.kinopoisk_staff_dto import KinopoiskStaffMemberDTO
from services.cast.parse_top_actors import MAX_TOP_ACTORS, parse_top_actors


def _staff_member(
    staff_id: int,
    *,
    profession_key: str,
    name_ru: str | None = None,
    name_en: str | None = None,
    description: str | None = None,
) -> KinopoiskStaffMemberDTO:
    return KinopoiskStaffMemberDTO(
        staff_id=staff_id,
        name_ru=name_ru,
        name_en=name_en,
        profession_key=profession_key,
        poster_url=None,
        description=description,
    )


def test_parse_top_actors_filters_and_preserves_order() -> None:
    staff = (
        _staff_member(1, profession_key='DIRECTOR', name_ru='Director'),
        _staff_member(2, profession_key='ACTOR', name_ru='Actor One', description=' Hero '),
        _staff_member(3, profession_key='ACTOR', name_en='Actor Two'),
        _staff_member(4, profession_key='PRODUCER', name_ru='Producer'),
        _staff_member(5, profession_key='ACTOR', name_ru='Actor Three'),
    )

    actors = parse_top_actors(staff)

    assert len(actors) == 3
    assert actors[0].kinopoisk_id == 2
    assert actors[0].billing_order == 1
    assert actors[0].role == 'Hero'
    assert actors[1].kinopoisk_id == 3
    assert actors[1].name == 'Actor Two'
    assert actors[2].kinopoisk_id == 5


def test_parse_top_actors_limits_to_ten() -> None:
    staff = tuple(
        _staff_member(i, profession_key='ACTOR', name_ru=f'Actor {i}') for i in range(1, 15)
    )

    actors = parse_top_actors(staff)

    assert len(actors) == MAX_TOP_ACTORS
    assert actors[0].kinopoisk_id == 1
    assert actors[-1].kinopoisk_id == 10


def test_parse_top_actors_skips_actors_without_name() -> None:
    staff = (
        _staff_member(1, profession_key='ACTOR', name_ru=None, name_en=None),
        _staff_member(2, profession_key='ACTOR', name_ru='Named'),
    )

    actors = parse_top_actors(staff)

    assert len(actors) == 1
    assert actors[0].kinopoisk_id == 2
    assert actors[0].billing_order == 1
