from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import Select, asc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from models.feed_post import FeedPost
from models.feed_post_comment import FeedPostComment
from models.user import User
from services.cards.list_movie_card_comments import MovieCardCommentAuthor
from services.feed_posts.get_feed_post_by_id import FeedPostNotFoundError
from services.reactions import GetReactionSummariesForTargetsService
from services.reactions.types import ReactionTargetSummary


@dataclass(frozen=True, slots=True)
class FeedPostCommentItem:
    id: int
    feed_post_id: int
    parent_comment_id: int | None
    text: str
    created_at: dt.datetime
    replies_count: int
    total_descendants_count: int
    author: MovieCardCommentAuthor
    reactions: ReactionTargetSummary


class CommentNotFoundError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class FeedPostCommentPage:
    items: list[FeedPostCommentItem]
    next_cursor: str | None


class ListFeedPostCommentsService:
    """Список комментариев к посту ленты (корни или ответы), с реакциями."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @classmethod
    def build(cls, session: AsyncSession) -> ListFeedPostCommentsService:
        return cls(session=session)

    async def execute(
        self,
        viewer_user_id: UUID,
        feed_post_id: int,
        parent_comment_id: int | None,
        cursor: int | None,
        limit: int,
        flat: bool = False,
    ) -> FeedPostCommentPage:
        post_exists = (
            await self._session.execute(select(FeedPost.id).where(FeedPost.id == feed_post_id))
        ).scalar_one_or_none()
        if post_exists is None:
            raise FeedPostNotFoundError()

        if parent_comment_id is not None:
            parent_pid = (
                await self._session.execute(
                    select(FeedPostComment.feed_post_id).where(
                        FeedPostComment.id == parent_comment_id
                    )
                )
            ).scalar_one_or_none()
            if parent_pid is None or parent_pid != feed_post_id:
                raise CommentNotFoundError()

        query: Select[tuple[FeedPostComment, User]] = (
            select(FeedPostComment, User)
            .join(User, User.id == FeedPostComment.user_id)
            .where(FeedPostComment.feed_post_id == feed_post_id)
            .order_by(asc(FeedPostComment.id))
            .limit(limit + 1)
        )
        if not flat and parent_comment_id is None:
            query = query.where(FeedPostComment.parent_comment_id.is_(None))
        elif parent_comment_id is not None:
            query = query.where(FeedPostComment.parent_comment_id == parent_comment_id)
        if cursor is not None:
            query = query.where(FeedPostComment.id > cursor)

        rows = (await self._session.execute(query)).all()
        has_more = len(rows) > limit
        visible_rows = rows[:limit]
        comment_ids = [c.id for c, _u in visible_rows]

        replies_count_by_comment: dict[int, int] = {}
        descendants_count_by_comment: dict[int, int] = {}
        if comment_ids:
            count_rows = (
                await self._session.execute(
                    select(
                        FeedPostComment.parent_comment_id,
                        func.count(FeedPostComment.id),
                    )
                    .where(FeedPostComment.parent_comment_id.in_(comment_ids))
                    .group_by(FeedPostComment.parent_comment_id)
                )
            ).all()
            for parent_id, count in count_rows:
                if parent_id is None:
                    continue
                replies_count_by_comment[parent_id] = int(count)

            descendants_seed = (
                select(
                    FeedPostComment.id.label('root_id'),
                    FeedPostComment.id.label('comment_id'),
                )
                .where(FeedPostComment.id.in_(comment_ids))
                .cte(name='fp_descendants_seed', recursive=True)
            )
            child_comment = aliased(FeedPostComment)
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

        _, _, fpc_summaries, _ = await GetReactionSummariesForTargetsService(self._session).execute(
            viewer_user_id=viewer_user_id,
            movie_card_ids=[],
            comment_ids=[],
            feed_post_comment_ids=comment_ids,
            feed_post_ids=[],
        )

        items = [
            FeedPostCommentItem(
                id=comment.id,
                feed_post_id=comment.feed_post_id,
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
                reactions=fpc_summaries[comment.id],
            )
            for comment, user in visible_rows
        ]
        next_cursor = str(visible_rows[-1][0].id) if has_more and visible_rows else None
        return FeedPostCommentPage(items=items, next_cursor=next_cursor)
