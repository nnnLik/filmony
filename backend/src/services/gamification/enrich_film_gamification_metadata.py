from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from providers.kinopoisk.kinopoisk_film_dto import KinopoiskFilmDTO
from providers.kinopoisk.kinopoisk_provider_transport import KinopoiskProviderTransport
from providers.kinopoisk.kinopoisk_sequels_dto import KinopoiskSequelFilmDTO
from providers.kinopoisk.kinopoisk_staff_dto import KinopoiskStaffMemberDTO


def _countries_from_film_dto(dto: KinopoiskFilmDTO) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for country in dto.countries:
        name = country.country.strip()
        if name == '':
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(name)
    return ordered


def _first_director(staff: tuple[KinopoiskStaffMemberDTO, ...]) -> KinopoiskStaffMemberDTO | None:
    for member in staff:
        if member.profession_key == 'DIRECTOR':
            return member
    return None


def _franchise_key(
    kinopoisk_id: int,
    sequels: tuple[KinopoiskSequelFilmDTO, ...],
) -> str:
    ids = {kinopoisk_id, *(item.film_id for item in sequels)}
    return f'kp_franchise:{min(ids)}'


@dataclass(frozen=True, slots=True)
class FilmGamificationMetadataPreview:
    countries: list[str]
    primary_director_kinopoisk_id: int | None
    primary_director_name: str | None
    primary_director_poster_url: str | None
    franchise_key: str | None


@dataclass
class EnrichFilmGamificationMetadataService:
    """Hydrates Film rows with Kinopoisk metadata used by profile gamification stamps.

    Persists production countries, a primary director, and a stable franchise cluster key
    derived from sequels/prequels so passport stamps and director marathons stay consistent.
    """

    _transport: KinopoiskProviderTransport

    class EnrichFilmGamificationMetadataError(Exception):
        pass

    @classmethod
    def build(
        cls,
        *,
        transport: KinopoiskProviderTransport | None = None,
    ) -> Self:
        return cls(_transport=transport or KinopoiskProviderTransport())

    async def execute(
        self,
        session: AsyncSession,
        film: Film,
        *,
        skip_staff: bool = False,
        skip_sequels: bool = False,
        film_dto: KinopoiskFilmDTO | None = None,
    ) -> None:
        _ = session
        preview = await self._build_preview(
            film.kinopoisk_id,
            skip_staff=skip_staff,
            skip_sequels=skip_sequels,
            film_dto=film_dto,
        )
        film.countries = preview.countries
        if not skip_staff:
            film.primary_director_kinopoisk_id = preview.primary_director_kinopoisk_id
            film.primary_director_name = preview.primary_director_name
            film.primary_director_poster_url = preview.primary_director_poster_url
        if not skip_sequels:
            film.franchise_key = preview.franchise_key

    async def preview(
        self,
        kinopoisk_id: int,
        *,
        skip_staff: bool = False,
        skip_sequels: bool = False,
        film_dto: KinopoiskFilmDTO | None = None,
    ) -> FilmGamificationMetadataPreview:
        return await self._build_preview(
            kinopoisk_id,
            skip_staff=skip_staff,
            skip_sequels=skip_sequels,
            film_dto=film_dto,
        )

    async def _build_preview(
        self,
        kinopoisk_id: int,
        *,
        skip_staff: bool,
        skip_sequels: bool,
        film_dto: KinopoiskFilmDTO | None,
    ) -> FilmGamificationMetadataPreview:
        dto = film_dto or await self._transport.get_film_by_id(kinopoisk_id)
        countries = _countries_from_film_dto(dto)

        director_id: int | None = None
        director_name: str | None = None
        director_poster_url: str | None = None
        if not skip_staff:
            staff = await self._transport.get_staff_by_film_id(kinopoisk_id)
            director = _first_director(staff)
            if director is not None:
                director_id = director.staff_id
                director_name = director.display_name()
                director_poster_url = director.poster_url

        franchise_key: str | None = None
        if not skip_sequels:
            sequels = await self._transport.get_sequels_and_prequels(kinopoisk_id)
            franchise_key = _franchise_key(kinopoisk_id, sequels)

        return FilmGamificationMetadataPreview(
            countries=countries,
            primary_director_kinopoisk_id=director_id,
            primary_director_name=director_name,
            primary_director_poster_url=director_poster_url,
            franchise_key=franchise_key,
        )


__all__ = (
    'EnrichFilmGamificationMetadataService',
    'FilmGamificationMetadataPreview',
)
