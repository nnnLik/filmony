from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.catalog_item import CatalogItem
from models.film import Film
from models.game import Game
from models.user import User
from models.user_card import UserCard
from services.cards.card_catalog_release_fields import universal_release_year_date
from services.search.ilike_escape import escape_ilike_pattern


@dataclass(frozen=True, slots=True)
class CatalogCardSearchHit:
    """Minimal user-card row for search results."""

    card_id: int
    title: str
    year: int | None
    poster_url: str | None
    summary: str | None
    rating: float
    author_profile_slug: str
    author_display_name: str | None
    author_username: str | None
    author_id: UUID


@dataclass
class SearchCatalogCardsService:
    """Finds existing user cards whose local title matches a free-text query."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, query: str, limit: int) -> list[CatalogCardSearchHit]:
        cap = max(1, min(limit, 80))
        pattern = f'%{escape_ilike_pattern(query)}%'
        title_match = or_(
            Film.title.ilike(pattern, escape='\\'),
            UserCard.display_title.ilike(pattern, escape='\\'),
        )
        film_pk = func.coalesce(UserCard.film_id, CatalogItem.film_id)
        stmt = (
            select(UserCard, User, Film, Game)
            .join(User, User.id == UserCard.user_id)
            .outerjoin(CatalogItem, CatalogItem.id == UserCard.catalog_item_id)
            .outerjoin(Film, Film.id == film_pk)
            .outerjoin(Game, Game.id == CatalogItem.game_id)
            .where(title_match)
            .order_by(UserCard.created_at.desc(), UserCard.id.desc())
            .limit(cap)
        )
        rows = (await self._session.execute(stmt)).all()
        result: list[CatalogCardSearchHit] = []
        for card, author, film, game in rows:
            display_title = (card.display_title or '').strip()
            if not display_title and film is not None:
                display_title = (film.title or '').strip()
            if not display_title:
                display_title = 'Untitled'

            poster_url = (card.display_cover_url or '').strip() or None
            if poster_url is None and film is not None and film.poster_url:
                poster_url = film.poster_url

            summary = (card.display_summary or '').strip() or None
            if summary is None and film is not None:
                summary = (film.short_description or '').strip() or None
            if summary is None and film is not None:
                summary = (film.description or '').strip() or None

            film_year = film.year if film is not None else None
            year, _ = universal_release_year_date(
                film_year=film_year,
                game_released=game.released if game is not None else None,
            )
            result.append(
                CatalogCardSearchHit(
                    card_id=int(card.id),
                    title=display_title,
                    year=year,
                    poster_url=poster_url,
                    summary=summary,
                    rating=float(card.rating),
                    author_profile_slug=author.profile_slug,
                    author_display_name=author.display_name,
                    author_username=author.username,
                    author_id=author.id,
                )
            )
        return result
