"""Local ILIKE search across the viewer's own library cards (film + manual titles)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.user_card import UserCard
from services.search.ilike_escape import escape_ilike_pattern


@dataclass(frozen=True, slots=True)
class MyUserCardTitleSearchHit:
    card_id: int
    title: str
    year: int | None
    poster_url: str | None
    film_id: int | None
    kinopoisk_id: int | None
    film_genres: list[str]


@dataclass
class SearchMyUserCardsByTitleService:
    """Returns the current user's cards whose resolved title matches a substring query."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, user_id: UUID, query: str, limit: int) -> list[MyUserCardTitleSearchHit]:
        cap = max(1, min(limit, 30))
        q = query.strip()
        pattern = f'%{escape_ilike_pattern(q)}%'
        title_for_row = func.coalesce(Film.title, UserCard.display_title, '')
        poster = func.coalesce(UserCard.display_cover_url, Film.poster_url)
        stmt = (
            select(
                UserCard.id,
                title_for_row,
                Film.year,
                poster,
                UserCard.film_id,
                Film.kinopoisk_id,
                Film.genres,
            )
            .outerjoin(Film, Film.id == UserCard.film_id)
            .where(UserCard.user_id == user_id)
            .where(
                or_(
                    Film.title.ilike(pattern, escape='\\'),
                    UserCard.display_title.ilike(pattern, escape='\\'),
                ),
            )
            .order_by(desc(UserCard.created_at), desc(UserCard.id))
            .limit(cap)
        )
        rows = (await self._session.execute(stmt)).all()
        hits: list[MyUserCardTitleSearchHit] = []
        for r in rows:
            raw_title = str(r[1] or '').strip()
            resolved = raw_title if raw_title else 'Untitled'
            film_id = int(r[4]) if r[4] is not None else None
            kp = int(r[5]) if r[5] is not None else None
            genres_val = r[6]
            genres = list(genres_val or []) if film_id is not None else []
            hits.append(
                MyUserCardTitleSearchHit(
                    card_id=int(r[0]),
                    title=resolved,
                    year=r[2],
                    poster_url=r[3],
                    film_id=film_id,
                    kinopoisk_id=kp,
                    film_genres=genres,
                ),
            )
        return hits
