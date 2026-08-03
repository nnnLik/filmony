from __future__ import annotations

import pytest

from models.film import Film
from providers.kinopoisk.kinopoisk_film_dto import KinopoiskCountryDTO, KinopoiskFilmDTO
from providers.kinopoisk.kinopoisk_sequels_dto import KinopoiskSequelFilmDTO
from providers.kinopoisk.kinopoisk_staff_dto import KinopoiskStaffMemberDTO
from services.gamification.enrich_film_gamification_metadata import (
    EnrichFilmGamificationMetadataService,
)


def _minimal_film_dto(*, kinopoisk_id: int = 301) -> KinopoiskFilmDTO:
    return KinopoiskFilmDTO(
        kinopoisk_id=kinopoisk_id,
        kinopoisk_hd_id=None,
        imdb_id=None,
        name_ru='Matrix',
        name_en='The Matrix',
        name_original=None,
        poster_url='https://example.com/p.jpg',
        poster_url_preview='https://example.com/p-preview.jpg',
        cover_url=None,
        logo_url=None,
        reviews_count=0,
        rating_good_review=None,
        rating_good_review_vote_count=None,
        rating_kinopoisk=None,
        rating_kinopoisk_vote_count=None,
        rating_imdb=None,
        rating_imdb_vote_count=None,
        rating_film_critics=None,
        rating_film_critics_vote_count=None,
        rating_await=None,
        rating_await_count=None,
        rating_rf_critics=None,
        rating_rf_critics_vote_count=None,
        web_url='https://example.com',
        year=1999,
        film_length=136,
        slogan=None,
        description=None,
        short_description=None,
        editor_annotation=None,
        is_tickets_available=False,
        production_status=None,
        film_kind='FILM',
        rating_mpaa=None,
        rating_age_limits=None,
        has_imax=None,
        has_3d=None,
        last_sync='2020-01-01',
        countries=(KinopoiskCountryDTO(country='США'), KinopoiskCountryDTO(country='Австралия')),
        genres=(),
        start_year=None,
        end_year=None,
        serial=None,
        short_film=None,
        completed=None,
    )


class FakeKinopoiskTransport:
    def __init__(
        self,
        *,
        film_dto: KinopoiskFilmDTO | None = None,
        staff: tuple[KinopoiskStaffMemberDTO, ...] = (),
        sequels: tuple[KinopoiskSequelFilmDTO, ...] = (),
    ) -> None:
        self._film_dto = film_dto or _minimal_film_dto()
        self._staff = staff
        self._sequels = sequels

    async def get_film_by_id(self, kinopoisk_id: int) -> KinopoiskFilmDTO:
        _ = kinopoisk_id
        return self._film_dto

    async def get_staff_by_film_id(self, kinopoisk_id: int) -> tuple[KinopoiskStaffMemberDTO, ...]:
        _ = kinopoisk_id
        return self._staff

    async def get_sequels_and_prequels(
        self,
        kinopoisk_id: int,
    ) -> tuple[KinopoiskSequelFilmDTO, ...]:
        _ = kinopoisk_id
        return self._sequels


@pytest.mark.asyncio
async def test_enrich_service_sets_countries_director_and_franchise_key() -> None:
    transport = FakeKinopoiskTransport(
        staff=(
            KinopoiskStaffMemberDTO(
                staff_id=10,
                name_ru='Лана Вачowski',
                name_en='Lana Wachowski',
                profession_key='ACTOR',
            ),
            KinopoiskStaffMemberDTO(
                staff_id=11,
                name_ru='Лана Вачowski',
                name_en='Lana Wachowski',
                profession_key='DIRECTOR',
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
    assert film.franchise_key == 'kp_franchise:301'


@pytest.mark.asyncio
async def test_enrich_service_preview_respects_skip_flags() -> None:
    transport = FakeKinopoiskTransport(
        staff=(
            KinopoiskStaffMemberDTO(
                staff_id=11,
                name_ru='Director',
                name_en=None,
                profession_key='DIRECTOR',
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
    transport = FakeKinopoiskTransport(sequels=())
    enricher = EnrichFilmGamificationMetadataService.build(transport=transport)
    preview = await enricher.preview(301)
    assert preview.franchise_key == 'kp_franchise:301'
