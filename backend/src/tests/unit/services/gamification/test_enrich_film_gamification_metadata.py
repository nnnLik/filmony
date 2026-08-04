from __future__ import annotations

import pytest

from models.film import Film
from providers.kinopoisk.kinopoisk_sequels_dto import KinopoiskSequelFilmDTO
from providers.kinopoisk.kinopoisk_staff_dto import KinopoiskStaffMemberDTO
from services.gamification.enrich_film_gamification_metadata import (
    EnrichFilmGamificationMetadataService,
)
from tests.support.fake_kinopoisk_gamification_transport import (
    FakeKinopoiskGamificationTransport,
    minimal_kinopoisk_film_dto,
)


@pytest.mark.asyncio
async def test_enrich_service_sets_countries_director_and_franchise_key() -> None:
    transport = FakeKinopoiskGamificationTransport(
        staff=(
            KinopoiskStaffMemberDTO(
                staff_id=10,
                name_ru='Лана Вачowski',
                name_en='Lana Wachowski',
                profession_key='ACTOR',
                poster_url=None,
            ),
            KinopoiskStaffMemberDTO(
                staff_id=11,
                name_ru='Лана Вачowski',
                name_en='Lana Wachowski',
                profession_key='DIRECTOR',
                poster_url='https://kinopoisk.example/staff/11.jpg',
            ),
        ),
        sequels=(
            KinopoiskSequelFilmDTO(film_id=302, name_ru='Reloaded', relation_type='SEQUEL'),
            KinopoiskSequelFilmDTO(film_id=303, name_ru='Revolutions', relation_type='SEQUEL'),
        ),
    )
    enricher = EnrichFilmGamificationMetadataService.build(transport=transport)
    film = Film(
        kinopoisk_id=301,
        title='Matrix',
        year=1999,
        poster_url=None,
        genres=[],
    )

    await enricher.execute(session=None, film=film)  # type: ignore[arg-type]

    assert film.countries == ['США', 'Австралия']
    assert film.primary_director_kinopoisk_id == 11
    assert film.primary_director_name == 'Лана Вачowski'
    assert film.primary_director_poster_url == 'https://kinopoisk.example/staff/11.jpg'
    assert film.franchise_key == 'kp_franchise:301'


@pytest.mark.asyncio
async def test_enrich_service_preview_respects_skip_flags() -> None:
    transport = FakeKinopoiskGamificationTransport(
        staff=(
            KinopoiskStaffMemberDTO(
                staff_id=11,
                name_ru='Director',
                name_en=None,
                profession_key='DIRECTOR',
                poster_url=None,
            ),
        ),
        sequels=(KinopoiskSequelFilmDTO(film_id=999, name_ru='Other', relation_type='SEQUEL'),),
    )
    enricher = EnrichFilmGamificationMetadataService.build(transport=transport)

    preview = await enricher.preview(301, skip_staff=True, skip_sequels=True)

    assert preview.countries == ['США', 'Австралия']
    assert preview.primary_director_kinopoisk_id is None
    assert preview.franchise_key is None


@pytest.mark.asyncio
async def test_enrich_service_franchise_key_uses_self_when_no_sequels() -> None:
    transport = FakeKinopoiskGamificationTransport(sequels=())
    enricher = EnrichFilmGamificationMetadataService.build(transport=transport)
    preview = await enricher.preview(301)
    assert preview.franchise_key == 'kp_franchise:301'
