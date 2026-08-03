"""Fake Kinopoisk transport for gamification/backfill tests — no outbound HTTP."""

from __future__ import annotations

from dataclasses import replace

from providers.kinopoisk.kinopoisk_film_dto import KinopoiskCountryDTO, KinopoiskFilmDTO
from providers.kinopoisk.kinopoisk_sequels_dto import KinopoiskSequelFilmDTO
from providers.kinopoisk.kinopoisk_staff_dto import KinopoiskStaffMemberDTO


def minimal_kinopoisk_film_dto(*, kinopoisk_id: int = 301) -> KinopoiskFilmDTO:
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


class FakeKinopoiskGamificationTransport:
    """Records calls; never hits Kinopoisk HTTP."""

    def __init__(
        self,
        *,
        film_dto: KinopoiskFilmDTO | None = None,
        staff: tuple[KinopoiskStaffMemberDTO, ...] = (),
        sequels: tuple[KinopoiskSequelFilmDTO, ...] = (),
    ) -> None:
        self._film_dto = film_dto or minimal_kinopoisk_film_dto()
        self._staff = staff
        self._sequels = sequels
        self.get_film_by_id_calls: list[int] = []
        self.get_staff_by_film_id_calls: list[int] = []
        self.get_sequels_and_prequels_calls: list[int] = []

    async def get_film_by_id(self, kinopoisk_id: int) -> KinopoiskFilmDTO:
        self.get_film_by_id_calls.append(kinopoisk_id)
        return replace(self._film_dto, kinopoisk_id=kinopoisk_id)

    async def get_staff_by_film_id(self, kinopoisk_id: int) -> tuple[KinopoiskStaffMemberDTO, ...]:
        self.get_staff_by_film_id_calls.append(kinopoisk_id)
        return self._staff

    async def get_sequels_and_prequels(
        self,
        kinopoisk_id: int,
    ) -> tuple[KinopoiskSequelFilmDTO, ...]:
        self.get_sequels_and_prequels_calls.append(kinopoisk_id)
        return self._sequels
