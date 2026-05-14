from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from utils.http_url import normalize_absolute_http_url


class KinopoiskFilmDtoParseError(Exception):
    """Невалидный или неполный JSON ответа ``/api/v2.2/films/{id}`` под схему ``Film``."""


@dataclass(frozen=True, slots=True)
class KinopoiskCountryDTO:
    country: str


@dataclass(frozen=True, slots=True)
class KinopoiskGenreDTO:
    genre: str


def _require_int(d: dict[str, Any], key: str) -> int:
    if key not in d:
        raise KinopoiskFilmDtoParseError(f'missing required field {key}')
    v = d[key]
    if isinstance(v, bool) or not isinstance(v, int):
        raise KinopoiskFilmDtoParseError(f'invalid int for {key}')
    return v


def _optional_int(d: dict[str, Any], key: str) -> int | None:
    if key not in d or d[key] is None:
        return None
    v = d[key]
    if isinstance(v, bool) or not isinstance(v, int):
        return None
    return v


def _optional_float(d: dict[str, Any], key: str) -> float | None:
    if key not in d or d[key] is None:
        return None
    v = d[key]
    if isinstance(v, bool):
        return None
    if isinstance(v, float):
        return v
    if isinstance(v, int):
        return float(v)
    return None


def _require_str(d: dict[str, Any], key: str) -> str:
    if key not in d:
        raise KinopoiskFilmDtoParseError(f'missing required field {key}')
    v = d[key]
    if not isinstance(v, str):
        raise KinopoiskFilmDtoParseError(f'invalid string for {key}')
    return v


def _optional_str(d: dict[str, Any], key: str) -> str | None:
    if key not in d or d[key] is None:
        return None
    v = d[key]
    if not isinstance(v, str):
        return None
    return v


def _require_bool(d: dict[str, Any], key: str) -> bool:
    if key not in d:
        raise KinopoiskFilmDtoParseError(f'missing required field {key}')
    v = d[key]
    if not isinstance(v, bool):
        raise KinopoiskFilmDtoParseError(f'invalid bool for {key}')
    return v


def _optional_bool(d: dict[str, Any], key: str) -> bool | None:
    if key not in d or d[key] is None:
        return None
    v = d[key]
    if not isinstance(v, bool):
        return None
    return v


def _require_url(d: dict[str, Any], key: str) -> str:
    raw = _require_str(d, key)
    normalized = normalize_absolute_http_url(raw)
    if normalized is None:
        raise KinopoiskFilmDtoParseError(f'invalid url for {key}')
    return normalized


def _optional_url(d: dict[str, Any], key: str) -> str | None:
    s = _optional_str(d, key)
    if s is None:
        return None
    return normalize_absolute_http_url(s)


def _countries_tuple(raw: Any) -> tuple[KinopoiskCountryDTO, ...]:
    if not isinstance(raw, list):
        return ()
    out: list[KinopoiskCountryDTO] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        c = item.get('country')
        if isinstance(c, str) and c.strip():
            out.append(KinopoiskCountryDTO(country=c.strip()))
    return tuple(out)


def _genres_tuple(raw: Any) -> tuple[KinopoiskGenreDTO, ...]:
    if not isinstance(raw, list):
        return ()
    out: list[KinopoiskGenreDTO] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        g = item.get('genre')
        if isinstance(g, str) and g.strip():
            out.append(KinopoiskGenreDTO(genre=g.strip()))
    return tuple(out)


@dataclass(frozen=True, slots=True)
class KinopoiskFilmDTO:
    """``#/components/schemas/Film`` — поля из ``properties`` (имена в Python — snake_case)."""

    kinopoisk_id: int
    kinopoisk_hd_id: str | None
    imdb_id: str | None
    name_ru: str | None
    name_en: str | None
    name_original: str | None
    poster_url: str
    poster_url_preview: str
    cover_url: str | None
    logo_url: str | None
    reviews_count: int
    rating_good_review: float | None
    rating_good_review_vote_count: int | None
    rating_kinopoisk: float | None
    rating_kinopoisk_vote_count: int | None
    rating_imdb: float | None
    rating_imdb_vote_count: int | None
    rating_film_critics: float | None
    rating_film_critics_vote_count: int | None
    rating_await: float | None
    rating_await_count: int | None
    rating_rf_critics: float | None
    rating_rf_critics_vote_count: int | None
    web_url: str
    year: int | None
    film_length: int | None
    slogan: str | None
    description: str | None
    short_description: str | None
    editor_annotation: str | None
    is_tickets_available: bool
    production_status: str | None
    film_kind: str
    rating_mpaa: str | None
    rating_age_limits: str | None
    has_imax: bool | None
    has_3d: bool | None
    last_sync: str
    countries: tuple[KinopoiskCountryDTO, ...]
    genres: tuple[KinopoiskGenreDTO, ...]
    start_year: int | None
    end_year: int | None
    serial: bool | None
    short_film: bool | None
    completed: bool | None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        return cls(
            kinopoisk_id=_require_int(d, 'kinopoiskId'),
            kinopoisk_hd_id=_optional_str(d, 'kinopoiskHDId'),
            imdb_id=_optional_str(d, 'imdbId'),
            name_ru=_optional_str(d, 'nameRu'),
            name_en=_optional_str(d, 'nameEn'),
            name_original=_optional_str(d, 'nameOriginal'),
            poster_url=_require_url(d, 'posterUrl'),
            poster_url_preview=_require_url(d, 'posterUrlPreview'),
            cover_url=_optional_url(d, 'coverUrl'),
            logo_url=_optional_url(d, 'logoUrl'),
            reviews_count=_require_int(d, 'reviewsCount'),
            rating_good_review=_optional_float(d, 'ratingGoodReview'),
            rating_good_review_vote_count=_optional_int(d, 'ratingGoodReviewVoteCount'),
            rating_kinopoisk=_optional_float(d, 'ratingKinopoisk'),
            rating_kinopoisk_vote_count=_optional_int(d, 'ratingKinopoiskVoteCount'),
            rating_imdb=_optional_float(d, 'ratingImdb'),
            rating_imdb_vote_count=_optional_int(d, 'ratingImdbVoteCount'),
            rating_film_critics=_optional_float(d, 'ratingFilmCritics'),
            rating_film_critics_vote_count=_optional_int(d, 'ratingFilmCriticsVoteCount'),
            rating_await=_optional_float(d, 'ratingAwait'),
            rating_await_count=_optional_int(d, 'ratingAwaitCount'),
            rating_rf_critics=_optional_float(d, 'ratingRfCritics'),
            rating_rf_critics_vote_count=_optional_int(d, 'ratingRfCriticsVoteCount'),
            web_url=_require_str(d, 'webUrl'),
            year=_optional_int(d, 'year'),
            film_length=_optional_int(d, 'filmLength'),
            slogan=_optional_str(d, 'slogan'),
            description=_optional_str(d, 'description'),
            short_description=_optional_str(d, 'shortDescription'),
            editor_annotation=_optional_str(d, 'editorAnnotation'),
            is_tickets_available=_require_bool(d, 'isTicketsAvailable'),
            production_status=_optional_str(d, 'productionStatus'),
            film_kind=_require_str(d, 'type'),
            rating_mpaa=_optional_str(d, 'ratingMpaa'),
            rating_age_limits=_optional_str(d, 'ratingAgeLimits'),
            has_imax=_optional_bool(d, 'hasImax'),
            has_3d=_optional_bool(d, 'has3D'),
            last_sync=_require_str(d, 'lastSync'),
            countries=_countries_tuple(d.get('countries')),
            genres=_genres_tuple(d.get('genres')),
            start_year=_optional_int(d, 'startYear'),
            end_year=_optional_int(d, 'endYear'),
            serial=_optional_bool(d, 'serial'),
            short_film=_optional_bool(d, 'shortFilm'),
            completed=_optional_bool(d, 'completed'),
        )
