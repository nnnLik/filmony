from __future__ import annotations

from dataclasses import dataclass
from typing import Any


class TmdbDtoParseError(Exception):
    """Invalid or incomplete TMDB JSON payload."""


def _require_int(d: dict[str, Any], key: str) -> int:
    if key not in d:
        raise TmdbDtoParseError(f'missing required field {key}')
    value = d[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise TmdbDtoParseError(f'invalid int for {key}')
    return value


def _optional_str(d: dict[str, Any], key: str) -> str | None:
    raw = d.get(key)
    if not isinstance(raw, str):
        return None
    text = raw.strip()
    return text if text else None


@dataclass(frozen=True, slots=True)
class TmdbCrewMemberDTO:
    id: int
    name: str
    job: str
    department: str


@dataclass(frozen=True, slots=True)
class TmdbCreditsDTO:
    id: int
    crew: tuple[TmdbCrewMemberDTO, ...]


def credits_from_dict(payload: dict[str, Any]) -> TmdbCreditsDTO:
    crew_raw = payload.get('crew')
    if not isinstance(crew_raw, list):
        crew_raw = []
    crew: list[TmdbCrewMemberDTO] = []
    for item in crew_raw:
        if not isinstance(item, dict):
            continue
        try:
            person_id = _require_int(item, 'id')
        except TmdbDtoParseError:
            continue
        name = _optional_str(item, 'name')
        job = _optional_str(item, 'job')
        department = _optional_str(item, 'department')
        if name is None or job is None or department is None:
            continue
        crew.append(
            TmdbCrewMemberDTO(
                id=person_id,
                name=name,
                job=job,
                department=department,
            ),
        )
    movie_id = _require_int(payload, 'id') if 'id' in payload else 0
    return TmdbCreditsDTO(id=movie_id, crew=tuple(crew))


__all__ = (
    'TmdbCreditsDTO',
    'TmdbCrewMemberDTO',
    'TmdbDtoParseError',
    'credits_from_dict',
)
