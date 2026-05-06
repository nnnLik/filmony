from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import Select, asc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from models.movie_card import MovieCard
from models.movie_card_comment import MovieCardComment
from models.user import User


@dataclass(frozen=True, slots=True)
class MovieCardCommentAuthor:
    id: UUID
    profile_slug: str
    username: str | None
    first_name: str | None
    last_name: str | None
    photo_url: str | None
    display_name: str | None


@dataclass(frozen=True, slots=True)
class MovieCardCommentItem:
    id: int
    movie_card_id: int
    parent_comment_id: int | None
    text: str
    created_at: dt.datetime
    replies_count: int
    total_descendants_count: int
    author: MovieCardCommentAuthor


class MovieCardNotFoundError(Exception):
    pass


class CommentNotFoundError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class MovieCardCommentPage:
    items: list[MovieCardCommentItem]
    next_cursor: str | None


class ListMovieCardCommentsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        card_id: int,
        parent_comment_id: int | None,
        cursor: int | None,
        limit: int,
        flat: bool = False,
    ) -> MovieCardCommentPage:
        card_exists = (
            await self._session.execute(select(MovieCard.id).where(MovieCard.id == card_id))
        ).scalar_one_or_none()
        if card_exists is None:
            raise MovieCardNotFoundError()

        if parent_comment_id is not None:
            parent_card_id = (
                await self._session.execute(
                    select(MovieCardComment.movie_card_id).where(
                        MovieCardComment.id == parent_comment_id
                    )
                )
            ).scalar_one_or_none()
            if parent_card_id is None or parent_card_id != card_id:
                raise CommentNotFoundError()

        query: Select[tuple[MovieCardComment, User]] = (
            select(MovieCardComment, User)
            .join(User, User.id == MovieCardComment.user_id)
            .where(MovieCardComment.movie_card_id == card_id)
            .order_by(asc(MovieCardComment.id))
            .limit(limit + 1)
        )
        if not flat and parent_comment_id is None:
            query = query.where(MovieCardComment.parent_comment_id.is_(None))
        elif parent_comment_id is not None:
            query = query.where(MovieCardComment.parent_comment_id == parent_comment_id)
        if cursor is not None:
            query = query.where(MovieCardComment.id > cursor)

        rows = (await self._session.execute(query)).all()
        has_more = len(rows) > limit
        visible_rows = rows[:limit]
        comment_ids = [comment.id for comment, _user in visible_rows]

        replies_count_by_comment: dict[int, int] = {}
        descendants_count_by_comment: dict[int, int] = {}
        if comment_ids:
            count_rows = (
                await self._session.execute(
                    select(
                        MovieCardComment.parent_comment_id,
                        func.count(MovieCardComment.id),
                    )
                    .where(MovieCardComment.parent_comment_id.in_(comment_ids))
                    .group_by(MovieCardComment.parent_comment_id)
                )
            ).all()
            for parent_id, count in count_rows:
                if parent_id is None:
                    continue
                replies_count_by_comment[parent_id] = int(count)

            descendants_seed = (
                select(
                    MovieCardComment.id.label('root_id'),
                    MovieCardComment.id.label('comment_id'),
                )
                .where(MovieCardComment.id.in_(comment_ids))
                .cte(name='descendants_seed', recursive=True)
            )
            child_comment = aliased(MovieCardComment)
            descendants_tree = descendants_seed.union_all(
                select(
                    descendants_seed.c.root_id,
                    child_comment.id.label('comment_id'),
                ).join(
                    child_comment,
                    child_comment.parent_comment_id == descendants_seed.c.comment_id,
                )
            )
            descendant_rows = (
                await self._session.execute(
                    select(
                        descendants_tree.c.root_id,
                        func.count(descendants_tree.c.comment_id),
                    )
                    .where(descendants_tree.c.comment_id != descendants_tree.c.root_id)
                    .group_by(descendants_tree.c.root_id)
                )
            ).all()
            for root_id, count in descendant_rows:
                descendants_count_by_comment[int(root_id)] = int(count)

        items = [
            MovieCardCommentItem(
                id=comment.id,
                movie_card_id=comment.movie_card_id,
                parent_comment_id=comment.parent_comment_id,
                text=comment.text,
                created_at=comment.created_at,
                replies_count=replies_count_by_comment.get(comment.id, 0),
                total_descendants_count=descendants_count_by_comment.get(comment.id, 0),
                author=MovieCardCommentAuthor(
                    id=user.id,
                    profile_slug=user.profile_slug,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    photo_url=user.photo_url,
                    display_name=user.display_name,
                ),
            )
            for comment, user in visible_rows
        ]
        next_cursor = str(visible_rows[-1][0].id) if has_more and visible_rows else None
        return MovieCardCommentPage(items=items, next_cursor=next_cursor)
