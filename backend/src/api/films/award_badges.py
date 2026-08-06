from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from api.films.schemas import FilmAwardBadgeResponse
from services.film_award_badges.list_film_award_badges import ListFilmAwardBadgesService


def _to_responses(badges) -> list[FilmAwardBadgeResponse]:
    return [
        FilmAwardBadgeResponse(kind=badge.kind.value, ceremony_year=badge.ceremony_year)
        for badge in badges
    ]


async def film_award_badge_responses(
    db: AsyncSession,
    film_id: int,
) -> list[FilmAwardBadgeResponse]:
    badges = await ListFilmAwardBadgesService.build(db).execute(film_id)
    return _to_responses(badges)


async def film_award_badge_responses_by_film_ids(
    db: AsyncSession,
    film_ids: list[int],
) -> dict[int, list[FilmAwardBadgeResponse]]:
    grouped = await ListFilmAwardBadgesService.build(db).execute_many(film_ids)
    return {film_id: _to_responses(badges) for film_id, badges in grouped.items()}
