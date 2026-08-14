from __future__ import annotations

from dataclasses import dataclass

import httpx

from conf import settings
from providers.shared_async_http import httpx_get_idempotent
from utils.http_url import normalize_absolute_http_url


class KinopoiskClientError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class KinopoiskFilmPayload:
    kinopoisk_id: int
    title: str
    year: int | None
    poster_url: str | None
    genres: list[str]
    countries: list[str]
    short_description: str | None
    description: str | None
    imdb_id: str | None
    film_length: int | None = None
    slogan: str | None = None
    rating_kinopoisk: float | None = None
    rating_imdb: float | None = None
    rating_age_limits: str | None = None


def _optional_int_field(payload: dict[str, object], key: str) -> int | None:
    raw = payload.get(key)
    if isinstance(raw, int):
        return raw
    if isinstance(raw, str) and raw.isdigit():
        return int(raw)
    return None


def _optional_float_field(payload: dict[str, object], key: str) -> float | None:
    raw = payload.get(key)
    if isinstance(raw, (int, float)):
        return float(raw)
    if isinstance(raw, str):
        try:
            return float(raw)
        except ValueError:
            return None
    return None


def _optional_text_field(payload: dict[str, object], key: str) -> str | None:
    raw = payload.get(key)
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    return text if text else None


def _parse_genres(payload: object) -> list[str]:
    if not isinstance(payload, list):
        return []
    genres: list[str] = []
    seen: set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        value = item.get('genre')
        if not isinstance(value, str):
            continue
        genre = value.strip()
        if genre == '':
            continue
        key = genre.lower()
        if key in seen:
            continue
        seen.add(key)
        genres.append(genre)
    return genres


def _parse_countries(payload: object) -> list[str]:
    if not isinstance(payload, list):
        return []
    countries: list[str] = []
    seen: set[str] = set()
    for item in payload:
        if not isinstance(item, dict):
            continue
        value = item.get('country')
        if not isinstance(value, str):
            continue
        country = value.strip()
        if country == '':
            continue
        key = country.lower()
        if key in seen:
            continue
        seen.add(key)
        countries.append(country)
    return countries


class KinopoiskClient:
    async def get_film(self, kinopoisk_id: int) -> KinopoiskFilmPayload:
        base = settings.kinopoisk.base_url.rstrip('/')
        url = f'{base}/v2.2/films/{kinopoisk_id}'
        headers = {'X-API-KEY': settings.kinopoisk.api_key}

        try:
            response = await httpx_get_idempotent(url, headers=headers)
        except httpx.HTTPError as exc:
            raise KinopoiskClientError('failed to fetch kinopoisk film') from exc

        if response.status_code != 200:
            raise KinopoiskClientError(f'kinopoisk returned {response.status_code}')

        try:
            payload_raw = response.json()
        except ValueError as exc:
            raise KinopoiskClientError('invalid kinopoisk response') from exc

        if not isinstance(payload_raw, dict):
            raise KinopoiskClientError('invalid kinopoisk response')
        payload: dict[str, object] = payload_raw

        title = payload.get('nameRu') or payload.get('nameOriginal') or payload.get('nameEn')
        if not isinstance(title, str) or title.strip() == '':
            raise KinopoiskClientError('kinopoisk title is missing')

        year_raw = payload.get('year')
        year = (
            int(year_raw) if isinstance(year_raw, int | str) and str(year_raw).isdigit() else None
        )
        poster_url = payload.get('posterUrl')
        genres = _parse_genres(payload.get('genres'))
        countries = _parse_countries(payload.get('countries'))
        poster_norm = normalize_absolute_http_url(
            poster_url if isinstance(poster_url, str) else None
        )
        short_description = _optional_text_field(payload, 'shortDescription')
        description = _optional_text_field(payload, 'description')
        imdb_raw = payload.get('imdbId')
        imdb_id = imdb_raw.strip() if isinstance(imdb_raw, str) and imdb_raw.strip() else None
        return KinopoiskFilmPayload(
            kinopoisk_id=kinopoisk_id,
            title=title.strip(),
            year=year,
            poster_url=poster_norm,
            genres=genres,
            countries=countries,
            short_description=short_description,
            description=description,
            imdb_id=imdb_id,
            film_length=_optional_int_field(payload, 'filmLength'),
            slogan=_optional_text_field(payload, 'slogan'),
            rating_kinopoisk=_optional_float_field(payload, 'ratingKinopoisk'),
            rating_imdb=_optional_float_field(payload, 'ratingImdb'),
            rating_age_limits=_optional_text_field(payload, 'ratingAgeLimits'),
        )
