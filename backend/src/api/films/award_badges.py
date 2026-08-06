from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from api.films.schemas import FilmAwardBadgeResponse
from services.film_award_badges.list_film_award_badges import ListFilmAwardBadgesService


async def film_award_badge_responses(
    db: AsyncSession,
    film_id: int,
) -> list[FilmAwardBadgeResponse]:
    badges = await ListFilmAwardBadgesService.build(db).execute(film_id)
    return [
        FilmAwardBadgeResponse(kind=badge.kind.value, ceremony_year=badge.ceremony_year)
        for badge in badges
    ]
