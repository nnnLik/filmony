from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from utils.http_url import normalize_absolute_http_url

from .kinopoisk_film_dto import (
    KinopoiskCountryDTO,
    KinopoiskFilmDtoParseError,
    KinopoiskGenreDTO,
    _countries_tuple,
    _genres_tuple,
    _optional_int,
    _optional_str,
    _require_int,
)


@dataclass(frozen=True, slots=True)
class KinopoiskFilmSearchItemDTO:
    """One row from ``#/components/schemas/FilmSearchResponse_films`` / keyword search."""

    kinopoisk_id: int
    name_ru: str | None
    name_en: str | None
    name_original: str | None
    film_kind: str | None
    year: str | None
    description: str | None
    poster_url: str | None
    poster_url_preview: str | None
    countries: tuple[KinopoiskCountryDTO, ...]
    genres: tuple[KinopoiskGenreDTO, ...]

    def display_title(self) -> str:
        for key in (self.name_ru, self.name_original, self.name_en):
            if isinstance(key, str) and key.strip():
                return key.strip()
        return ''

    def year_as_int(self) -> int | None:
        raw = self.year
        if not raw or not isinstance(raw, str):
            return None
        chunk = raw.strip().split('-', maxsplit=1)[0].strip()
        if chunk.isdigit() and len(chunk) == 4:
            return int(chunk)
        return None

    def poster_url_normalized(self) -> str | None:
        raw = self.poster_url if self.poster_url else self.poster_url_preview
        if not raw:
            return None
        return normalize_absolute_http_url(raw)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        if not isinstance(d, dict):
            raise KinopoiskFilmDtoParseError('film search item must be an object')
        return cls(
            kinopoisk_id=_require_int(d, 'filmId'),
            name_ru=_optional_str(d, 'nameRu'),
            name_en=_optional_str(d, 'nameEn'),
            name_original=_optional_str(d, 'nameOriginal'),
            film_kind=_optional_str(d, 'type'),
            year=_optional_str(d, 'year'),
            description=_optional_str(d, 'description'),
            poster_url=_optional_str(d, 'posterUrl'),
            poster_url_preview=_optional_str(d, 'posterUrlPreview'),
            countries=_countries_tuple(d.get('countries')),
            genres=_genres_tuple(d.get('genres')),
        )


@dataclass(frozen=True, slots=True)
class KinopoiskFilmSearchResponseDTO:
    """``#/components/schemas/FilmSearchResponse``."""

    keyword: str
    pages_count: int
    search_films_count_result: int
    films: tuple[KinopoiskFilmSearchItemDTO, ...]

    @classmethod
    def empty(cls, keyword: str) -> Self:
        return cls(
            keyword=keyword,
            pages_count=0,
            search_films_count_result=0,
            films=(),
        )

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        films_raw = d.get('films')
        if not isinstance(films_raw, list):
            raise KinopoiskFilmDtoParseError('films must be a list')
        films: list[KinopoiskFilmSearchItemDTO] = []
        for item in films_raw:
            if not isinstance(item, dict):
                continue
            try:
                films.append(KinopoiskFilmSearchItemDTO.from_dict(item))
            except KinopoiskFilmDtoParseError:
                continue
        keyword = _optional_str(d, 'keyword') or ''
        pages = _optional_int(d, 'pagesCount')
        total = _optional_int(d, 'searchFilmsCountResult')
        if pages is None:
            raise KinopoiskFilmDtoParseError('missing pagesCount')
        if total is None:
            raise KinopoiskFilmDtoParseError('missing searchFilmsCountResult')
        return cls(
            keyword=keyword,
            pages_count=pages,
            search_films_count_result=total,
            films=tuple(films),
        )


def genres_for_film_model(item: KinopoiskFilmSearchItemDTO) -> list[str]:
    ordered: list[str] = []
    seen: set[str] = set()
    for g in item.genres:
        name = g.genre.strip()
        if name == '':
            continue
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        ordered.append(name)
    return ordered
