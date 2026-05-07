from __future__ import annotations

from dataclasses import dataclass

import httpx

from conf import settings
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


class KinopoiskClient:
    async def get_film(self, kinopoisk_id: int) -> KinopoiskFilmPayload:
        base = settings.kinopoisk.base_url.rstrip('/')
        url = f'{base}/v2.2/films/{kinopoisk_id}'
        headers = {'X-API-KEY': settings.kinopoisk.api_key}
        timeout = settings.kinopoisk.timeout_seconds

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, headers=headers)
        except httpx.HTTPError as exc:
            raise KinopoiskClientError('failed to fetch kinopoisk film') from exc

        if response.status_code != 200:
            raise KinopoiskClientError(f'kinopoisk returned {response.status_code}')

        try:
            payload = response.json()
        except ValueError as exc:
            raise KinopoiskClientError('invalid kinopoisk response') from exc

        title = payload.get('nameRu') or payload.get('nameOriginal') or payload.get('nameEn')
        if not isinstance(title, str) or title.strip() == '':
            raise KinopoiskClientError('kinopoisk title is missing')

        year_raw = payload.get('year')
        year = (
            int(year_raw) if isinstance(year_raw, int | str) and str(year_raw).isdigit() else None
        )
        poster_url = payload.get('posterUrl')
        genres = _parse_genres(payload.get('genres'))
        poster_norm = normalize_absolute_http_url(
            poster_url if isinstance(poster_url, str) else None
        )
        return KinopoiskFilmPayload(
            kinopoisk_id=kinopoisk_id,
            title=title.strip(),
            year=year,
            poster_url=poster_norm,
            genres=genres,
        )
