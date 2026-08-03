from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from .kinopoisk_film_dto import (
    KinopoiskFilmDtoParseError,
    _optional_str,
    _require_int,
)


@dataclass(frozen=True, slots=True)
class KinopoiskSequelFilmDTO:
    """One row from ``GET /v2.1/films/{id}/sequels_and_prequels``."""

    film_id: int
    name_ru: str | None
    relation_type: str | None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        return cls(
            film_id=_require_int(d, 'filmId'),
            name_ru=_optional_str(d, 'nameRu'),
            relation_type=_optional_str(d, 'relationType'),
        )


def sequel_films_from_list(raw: Any) -> tuple[KinopoiskSequelFilmDTO, ...]:
    if not isinstance(raw, list):
        raise KinopoiskFilmDtoParseError('sequels response must be a list')
    out: list[KinopoiskSequelFilmDTO] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            out.append(KinopoiskSequelFilmDTO.from_dict(item))
        except KinopoiskFilmDtoParseError:
            continue
    return tuple(out)
