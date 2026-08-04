from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from .tmdb_credits_dto import TmdbDtoParseError
from .tmdb_movie_dto import TmdbMovieDetailDTO, movie_detail_from_dict


def _require_int(d: dict[str, Any], key: str) -> int:
    if key not in d:
        raise TmdbDtoParseError(f'missing required field {key}')
    value = d[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise TmdbDtoParseError(f'invalid int for {key}')
    return value


@dataclass(frozen=True, slots=True)
class TmdbFindMovieResultDTO:
    id: int
    title: str
    release_date: str | None


@dataclass(frozen=True, slots=True)
class TmdbFindResponseDTO:
    movie_results: tuple[TmdbFindMovieResultDTO, ...]

    @classmethod
    def empty(cls) -> TmdbFindResponseDTO:
        return cls(movie_results=())

    def first_movie_id(self) -> int | None:
        if not self.movie_results:
            return None
        return self.movie_results[0].id


def _movie_results_from_list(raw: object) -> tuple[TmdbFindMovieResultDTO, ...]:
    if not isinstance(raw, list):
        return ()
    results: list[TmdbFindMovieResultDTO] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            movie_id = _require_int(item, 'id')
        except TmdbDtoParseError:
            continue
        title = item.get('title')
        if not isinstance(title, str) or title.strip() == '':
            title = item.get('original_title')
        if not isinstance(title, str) or title.strip() == '':
            continue
        release_date = item.get('release_date')
        release = release_date.strip() if isinstance(release_date, str) else None
        results.append(
            TmdbFindMovieResultDTO(
                id=movie_id,
                title=title.strip(),
                release_date=release if release else None,
            ),
        )
    return tuple(results)


def find_response_from_dict(payload: dict[str, Any]) -> TmdbFindResponseDTO:
    return TmdbFindResponseDTO(
        movie_results=_movie_results_from_list(payload.get('movie_results')),
    )


def search_response_from_dict(payload: dict[str, Any]) -> TmdbFindResponseDTO:
    return TmdbFindResponseDTO(
        movie_results=_movie_results_from_list(payload.get('results')),
    )


__all__ = (
    'TmdbFindMovieResultDTO',
    'TmdbFindResponseDTO',
    'find_response_from_dict',
    'search_response_from_dict',
)
