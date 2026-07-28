from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.feed_post import FeedPost
from models.feed_post_comment import FeedPostComment
from services.cards.comment_reaction_tokens import (
    CommentReactionTokenError,
    validate_comment_text_with_reaction_tokens,
)
from services.feed_posts.get_feed_post_by_id import FeedPostNotFoundError


@dataclass(frozen=True, slots=True)
class CreateFeedPostCommentInput:
    text: str
    parent_comment_id: int | None


class ParentCommentNotFoundError(Exception):
    pass


class ParentCommentMismatchError(Exception):
    pass


class FeedPostCommentValidationError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class CreateFeedPostCommentResult:
    comment: FeedPostComment
    mentioned_user_ids: tuple[UUID, ...]


async def _normalize_text(
    value: str, session: AsyncSession, author_user_id: UUID
) -> tuple[str, tuple[UUID, ...]]:
    try:
        return await validate_comment_text_with_reaction_tokens(
            value, session, author_user_id=author_user_id
        )
    except CommentReactionTokenError as e:
        raise FeedPostCommentValidationError(str(e)) from e


class CreateFeedPostCommentService:
    """Создаёт комментарий под текстовым постом ленты (ветка через parent_comment_id)."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @classmethod
    def build(cls, session: AsyncSession) -> CreateFeedPostCommentService:
        return cls(session=session)

    async def execute(
        self,
        feed_post_id: int,
        user_id: UUID,
        payload: CreateFeedPostCommentInput,
    ) -> CreateFeedPostCommentResult:
        text, mentioned_user_ids = await _normalize_text(payload.text, self._session, user_id)
        post_exists = (
            await self._session.execute(select(FeedPost.id).where(FeedPost.id == feed_post_id))
        ).scalar_one_or_none()
        if post_exists is None:
            raise FeedPostNotFoundError()

        if payload.parent_comment_id is not None:
            parent_post_id = (
                await self._session.execute(
                    select(FeedPostComment.feed_post_id).where(
                        FeedPostComment.id == payload.parent_comment_id
                    )
                )
            ).scalar_one_or_none()
            if parent_post_id is None:
                raise ParentCommentNotFoundError()
            if parent_post_id != feed_post_id:
                raise ParentCommentMismatchError()

        comment = FeedPostComment(
            feed_post_id=feed_post_id,
            user_id=user_id,
            parent_comment_id=payload.parent_comment_id,
            text=text,
        )
        self._session.add(comment)
        await self._session.commit()
        await self._session.refresh(comment)
        return CreateFeedPostCommentResult(comment=comment, mentioned_user_ids=mentioned_user_ids)
