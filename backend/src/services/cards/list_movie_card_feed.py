from __future__ import annotations

from dataclasses import dataclass
from typing import cast
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.movie_card import MovieCard
from models.movie_card_comment import MovieCardComment
from models.movie_card_tag import MovieCardTag
from models.user import User
from services.cards.list_movie_card_comments import MovieCardCommentAuthor, MovieCardCommentItem


@dataclass(frozen=True, slots=True)
class MovieCardFeedItem:
    id: int
    user_id: UUID
    card_author: MovieCardCommentAuthor
    film_id: int
    film_kinopoisk_id: int
    film_genres: list[str]
    film_title: str
    film_year: int | None
    film_poster_url: str | None
    rating: float
    company: str
    mood_before: str
    mood_after: str
    custom_tags: list[str]
    comments_count: int
    comments_preview: list[MovieCardCommentItem]


@dataclass(frozen=True, slots=True)
class MovieCardFeedPage:
    items: list[MovieCardFeedItem]
    next_cursor: str | None


class ListMovieCardFeedService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, cursor: str | None, limit: int) -> MovieCardFeedPage:
        query = (
            select(MovieCard, Film, User)
            .join(Film, Film.id == MovieCard.film_id)
            .join(User, User.id == MovieCard.user_id)
            .order_by(MovieCard.id.desc())
            .limit(limit + 1)
        )
        if cursor is not None and cursor != '':
            query = query.where(MovieCard.id < int(cursor))

        rows = (await self._session.execute(query)).all()
        has_more = len(rows) > limit
        visible_rows = rows[:limit]
        card_ids = [card.id for card, _film, _author in visible_rows]

        tags_by_card: dict[int, list[str]] = {}
        if card_ids:
            tags_rows = (
                await self._session.execute(
                    select(MovieCardTag.movie_card_id, MovieCardTag.tag)
                    .where(MovieCardTag.movie_card_id.in_(card_ids))
                    .order_by(MovieCardTag.movie_card_id, MovieCardTag.tag)
                )
            ).all()
            for card_id_val, tag in tags_rows:
                tags_by_card.setdefault(card_id_val, []).append(tag)

        counts_by_card: dict[int, int] = dict.fromkeys(card_ids, 0)
        if card_ids:
            count_rows = (
                await self._session.execute(
                    select(MovieCardComment.movie_card_id, func.count(MovieCardComment.id))
                    .where(MovieCardComment.movie_card_id.in_(card_ids))
                    .group_by(MovieCardComment.movie_card_id)
                )
            ).all()
            for card_id_val, cnt in count_rows:
                counts_by_card[card_id_val] = int(cnt)

        previews_by_card: dict[int, list[MovieCardCommentItem]] = {cid: [] for cid in card_ids}
        if card_ids:
            ranked = (
                select(
                    MovieCardComment.id,
                    MovieCardComment.movie_card_id,
                    MovieCardComment.user_id,
                    MovieCardComment.parent_comment_id,
                    MovieCardComment.text,
                    MovieCardComment.created_at,
                    func.row_number()
                    .over(
                        partition_by=MovieCardComment.movie_card_id,
                        order_by=MovieCardComment.id.desc(),
                    )
                    .label('rn'),
                ).where(MovieCardComment.movie_card_id.in_(card_ids))
            ).subquery()

            preview_stmt = (
                select(
                    ranked.c.id,
                    ranked.c.movie_card_id,
                    ranked.c.parent_comment_id,
                    ranked.c.text,
                    ranked.c.created_at,
                    User,
                )
                .join(User, User.id == ranked.c.user_id)
                .where(ranked.c.rn <= 3)
                .order_by(ranked.c.movie_card_id.asc(), ranked.c.id.asc())
            )

            preview_rows = (await self._session.execute(preview_stmt)).all()
            for (
                cid,
                movie_card_id,
                parent_comment_id,
                text,
                created_at,
                author_row,
            ) in preview_rows:
                previews_by_card[movie_card_id].append(
                    MovieCardCommentItem(
                        id=cid,
                        movie_card_id=movie_card_id,
                        parent_comment_id=parent_comment_id,
                        text=text,
                        created_at=created_at,
                        replies_count=0,
                        total_descendants_count=0,
                        author=MovieCardCommentAuthor(
                            id=author_row.id,
                            profile_slug=author_row.profile_slug,
                            username=author_row.username,
                            first_name=author_row.first_name,
                            last_name=author_row.last_name,
                            photo_url=author_row.photo_url,
                            display_name=author_row.display_name,
                        ),
                    )
                )

        items = [
            MovieCardFeedItem(
                id=card.id,
                user_id=card.user_id,
                card_author=MovieCardCommentAuthor(
                    id=card_author_user.id,
                    profile_slug=card_author_user.profile_slug,
                    username=card_author_user.username,
                    first_name=card_author_user.first_name,
                    last_name=card_author_user.last_name,
                    photo_url=card_author_user.photo_url,
                    display_name=card_author_user.display_name,
                ),
                film_id=film.id,
                film_kinopoisk_id=film.kinopoisk_id,
                film_genres=list(film.genres or []),
                film_title=film.title,
                film_year=film.year,
                film_poster_url=film.poster_url,
                rating=float(card.rating),
                company=card.company,
                mood_before=card.mood_before,
                mood_after=card.mood_after,
                custom_tags=tags_by_card.get(card.id, []),
                comments_count=counts_by_card.get(card.id, 0),
                comments_preview=previews_by_card.get(card.id, []),
            )
            for card, film, card_author_user in visible_rows
        ]
        next_cursor = str(cast(int, visible_rows[-1][0].id)) if has_more and visible_rows else None
        return MovieCardFeedPage(items=items, next_cursor=next_cursor)
