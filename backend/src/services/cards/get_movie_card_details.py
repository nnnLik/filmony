from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.catalog_item import CatalogItem
from models.film import Film
from models.movie_card import MovieCard
from models.movie_card_tag import MovieCardTag
from models.user import User
from services.cards.list_movie_card_comments import MovieCardCommentAuthor
from services.reactions import GetReactionSummariesForTargetsService
from services.reactions.types import ReactionTargetSummary


@dataclass(frozen=True, slots=True)
class MovieCardDetails:
    id: int
    user_id: UUID
    card_author: MovieCardCommentAuthor
    film_id: int | None
    film_kinopoisk_id: int | None
    film_genres: list[str]
    film_title: str
    film_year: int | None
    film_poster_url: str | None
    film_short_description: str | None
    film_description: str | None
    catalog_item_id: int | None
    display_title: str
    display_cover_url: str | None
    display_summary: str | None
    rating: float
    company: str
    mood_before: str
    mood_after: str
    watch_note: str
    custom_tags: list[str]
    reactions: ReactionTargetSummary
    is_favorite: bool


class MovieCardNotFoundError(Exception):
    pass


class GetMovieCardDetailsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, card_id: int, viewer_user_id: UUID) -> MovieCardDetails:
        row = (
            await self._session.execute(
                select(MovieCard, User)
                .join(User, User.id == MovieCard.user_id)
                .where(MovieCard.id == card_id)
            )
        ).one_or_none()
        if row is None:
            raise MovieCardNotFoundError()
        card, author = row

        film: Film | None = None
        if card.film_id is not None:
            film = (
                await self._session.execute(select(Film).where(Film.id == card.film_id))
            ).scalar_one_or_none()
        elif card.catalog_item_id is not None:
            ci = (
                await self._session.execute(
                    select(CatalogItem).where(CatalogItem.id == card.catalog_item_id)
                )
            ).scalar_one_or_none()
            if ci is not None and ci.film_id is not None:
                film = (
                    await self._session.execute(select(Film).where(Film.id == ci.film_id))
                ).scalar_one_or_none()

        display_title = (card.display_title or '').strip()
        if not display_title and film is not None:
            display_title = (film.title or '').strip()
        if not display_title:
            display_title = 'Untitled'

        film_title_deprecated = film.title if film is not None else display_title

        tags = (
            (
                await self._session.execute(
                    select(MovieCardTag.tag)
                    .where(MovieCardTag.movie_card_id == card.id)
                    .order_by(MovieCardTag.tag)
                )
            )
            .scalars()
            .all()
        )
        summaries, _, _, _ = await GetReactionSummariesForTargetsService(self._session).execute(
            viewer_user_id=viewer_user_id,
            movie_card_ids=[card.id],
            comment_ids=[],
            feed_post_comment_ids=[],
            feed_post_ids=[],
        )
        return MovieCardDetails(
            id=card.id,
            user_id=card.user_id,
            card_author=MovieCardCommentAuthor(
                id=author.id,
                profile_slug=author.profile_slug,
                username=author.username,
                first_name=author.first_name,
                last_name=author.last_name,
                photo_url=author.photo_url,
                display_name=author.display_name,
            ),
            film_id=film.id if film is not None else None,
            film_kinopoisk_id=film.kinopoisk_id if film is not None else None,
            film_genres=list(film.genres or []) if film is not None else [],
            film_title=film_title_deprecated,
            film_year=film.year if film is not None else None,
            film_poster_url=film.poster_url if film is not None else None,
            film_short_description=film.short_description if film is not None else None,
            film_description=film.description if film is not None else None,
            catalog_item_id=card.catalog_item_id,
            display_title=display_title,
            display_cover_url=card.display_cover_url,
            display_summary=card.display_summary,
            rating=float(card.rating),
            company=card.company,
            mood_before=card.mood_before,
            mood_after=card.mood_after,
            watch_note=card.watch_note or '',
            custom_tags=list(tags),
            reactions=summaries[card.id],
            is_favorite=bool(card.is_favorite),
        )
