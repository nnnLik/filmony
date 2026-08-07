from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Self

from .kinopoisk_film_dto import (
    KinopoiskFilmDtoParseError,
    _optional_str,
    _require_int,
)


@dataclass(frozen=True, slots=True)
class KinopoiskStaffMemberDTO:
    """One row from ``GET /v1/staff?filmId={id}``."""

    staff_id: int
    name_ru: str | None
    name_en: str | None
    profession_key: str | None
    poster_url: str | None
    description: str | None = None

    def display_name(self) -> str | None:
        for key in (self.name_ru, self.name_en):
            if isinstance(key, str) and key.strip():
                return key.strip()
        return None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> Self:
        return cls(
            staff_id=_require_int(d, 'staffId'),
            name_ru=_optional_str(d, 'nameRu'),
            name_en=_optional_str(d, 'nameEn'),
            profession_key=_optional_str(d, 'professionKey'),
            poster_url=_optional_str(d, 'posterUrl'),
            description=_optional_str(d, 'description'),
        )


def staff_members_from_list(raw: Any) -> tuple[KinopoiskStaffMemberDTO, ...]:
    if not isinstance(raw, list):
        raise KinopoiskFilmDtoParseError('staff response must be a list')
    out: list[KinopoiskStaffMemberDTO] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        try:
            out.append(KinopoiskStaffMemberDTO.from_dict(item))
        except KinopoiskFilmDtoParseError:
            continue
    return tuple(out)
