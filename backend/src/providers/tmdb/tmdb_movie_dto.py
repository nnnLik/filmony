from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from conf import settings

from .tmdb_credits_dto import TmdbCreditsDTO, TmdbDtoParseError, credits_from_dict


def _require_int(d: dict[str, Any], key: str) -> int:
    if key not in d:
        raise TmdbDtoParseError(f'missing required field {key}')
    value = d[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise TmdbDtoParseError(f'invalid int for {key}')
    return value


def _optional_int(d: dict[str, Any], key: str) -> int | None:
    if key not in d or d[key] is None:
        return None
    value = d[key]
    if isinstance(value, bool) or not isinstance(value, int):
        return None
    return value


def _optional_str(d: dict[str, Any], key: str) -> str | None:
    raw = d.get(key)
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    return text if text else None


@dataclass(frozen=True, slots=True)
class TmdbProductionCountryDTO:
    iso_3166_1: str
    name: str


@dataclass(frozen=True, slots=True)
class TmdbCollectionRefDTO:
    id: int
    name: str
    poster_path: str | None
    backdrop_path: str | None


@dataclass(frozen=True, slots=True)
class TmdbMovieDetailDTO:
    id: int
    title: str
    original_title: str | None
    overview: str | None
    release_date: str | None
    poster_path: str | None
    imdb_id: str | None
    belongs_to_collection: TmdbCollectionRefDTO | None
    production_countries: tuple[TmdbProductionCountryDTO, ...]
    credits: TmdbCreditsDTO | None
    raw: dict[str, Any]

    def poster_url(self) -> str | None:
        if self.poster_path is None or self.poster_path.strip() == '':
            return None
        base = settings.tmdb.image_base_url.rstrip('/')
        path = self.poster_path if self.poster_path.startswith('/') else f'/{self.poster_path}'
        return f'{base}{path}'

    def release_year(self) -> int | None:
        if self.release_date is None or len(self.release_date) < 4:
            return None
        year_text = self.release_date[:4]
        if not year_text.isdigit():
            return None
        return int(year_text)


def _collection_from_dict(raw: object) -> TmdbCollectionRefDTO | None:
    if not isinstance(raw, dict):
        return None
    collection_id = _optional_int(raw, 'id')
    name = _optional_str(raw, 'name')
    if collection_id is None or name is None:
        return None
    return TmdbCollectionRefDTO(
        id=collection_id,
        name=name,
        poster_path=_optional_str(raw, 'poster_path'),
        backdrop_path=_optional_str(raw, 'backdrop_path'),
    )


def _production_countries_from_list(raw: object) -> tuple[TmdbProductionCountryDTO, ...]:
    if not isinstance(raw, list):
        return ()
    countries: list[TmdbProductionCountryDTO] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        iso = _optional_str(item, 'iso_3166_1')
        name = _optional_str(item, 'name')
        if iso is None or name is None:
            continue
        countries.append(TmdbProductionCountryDTO(iso_3166_1=iso, name=name))
    return tuple(countries)


def movie_detail_from_dict(payload: dict[str, Any]) -> TmdbMovieDetailDTO:
    movie_id = _require_int(payload, 'id')
    title = _optional_str(payload, 'title')
    if title is None:
        title = _optional_str(payload, 'original_title')
    if title is None:
        raise TmdbDtoParseError('missing movie title')

    credits_raw = payload.get('credits')
    credits = credits_from_dict(credits_raw) if isinstance(credits_raw, dict) else None

    external_ids = payload.get('external_ids')
    imdb_id = _optional_str(payload, 'imdb_id')
    if imdb_id is None and isinstance(external_ids, dict):
        imdb_id = _optional_str(external_ids, 'imdb_id')

    return TmdbMovieDetailDTO(
        id=movie_id,
        title=title,
        original_title=_optional_str(payload, 'original_title'),
        overview=_optional_str(payload, 'overview'),
        release_date=_optional_str(payload, 'release_date'),
        poster_path=_optional_str(payload, 'poster_path'),
        imdb_id=imdb_id,
        belongs_to_collection=_collection_from_dict(payload.get('belongs_to_collection')),
        production_countries=_production_countries_from_list(payload.get('production_countries')),
        credits=credits,
        raw=payload,
    )


__all__ = (
    'TmdbCollectionRefDTO',
    'TmdbMovieDetailDTO',
    'TmdbProductionCountryDTO',
    'movie_detail_from_dict',
)
