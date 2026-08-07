from __future__ import annotations

from dataclasses import dataclass

from providers.kinopoisk.kinopoisk_staff_dto import KinopoiskStaffMemberDTO

MAX_TOP_ACTORS = 10


@dataclass(frozen=True, slots=True)
class ParsedTopActor:
    kinopoisk_id: int
    name: str
    poster_url: str | None
    billing_order: int
    role: str | None


def parse_top_actors(staff: tuple[KinopoiskStaffMemberDTO, ...]) -> tuple[ParsedTopActor, ...]:
    """Return up to 10 ACTOR rows in Kinopoisk response order."""
    actors: list[ParsedTopActor] = []
    billing_order = 0
    for member in staff:
        if member.profession_key != 'ACTOR':
            continue
        name = member.display_name()
        if name is None:
            continue
        billing_order += 1
        if billing_order > MAX_TOP_ACTORS:
            break
        role: str | None = None
        if member.description is not None:
            trimmed = member.description.strip()
            if trimmed:
                role = trimmed
        actors.append(
            ParsedTopActor(
                kinopoisk_id=member.staff_id,
                name=name,
                poster_url=member.poster_url,
                billing_order=billing_order,
                role=role,
            ),
        )
    return tuple(actors)
