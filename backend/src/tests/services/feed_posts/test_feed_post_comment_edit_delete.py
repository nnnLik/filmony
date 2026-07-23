"""Service coverage for feed post comment update and delete."""

from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from core.database import get_session_factory
from models.feed_post import FeedPost
from models.feed_post_comment import FeedPostComment
from models.user import User
from services.feed_posts.delete_feed_post_comment import (
    DeleteFeedPostCommentService,
    FeedPostCommentForbiddenError as DeleteFeedPostCommentForbiddenError,
    FeedPostCommentMismatchError as DeleteFeedPostCommentMismatchError,
    FeedPostCommentNotFoundError as DeleteFeedPostCommentNotFoundError,
)
from services.feed_posts.update_feed_post_comment import (
    FeedPostCommentForbiddenError,
    FeedPostCommentMismatchError,
    FeedPostCommentNotFoundError,
    FeedPostCommentValidationError,
    UpdateFeedPostCommentService,
)


async def _create_user(*, telegram_user_id: int) -> User:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            telegram_user_id=telegram_user_id,
            profile_slug=f'fpc-{telegram_user_id}',
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def _create_post(user_id: UUID, *, body: str = 'post body') -> FeedPost:
    session_factory = get_session_factory()
    async with session_factory() as session:
        post = FeedPost(user_id=user_id, body=body)
        session.add(post)
        await session.commit()
        await session.refresh(post)
        return post


async def _create_comment(*, post_id: int, user_id: UUID, text: str = 'comment') -> FeedPostComment:
    session_factory = get_session_factory()
    async with session_factory() as session:
        comment = FeedPostComment(feed_post_id=post_id, user_id=user_id, text=text)
        session.add(comment)
        await session.commit()
        await session.refresh(comment)
        return comment


@pytest.mark.asyncio
async def test_update_feed_post_comment_not_found(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=891001)
    post = await _create_post(user.id)
    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = UpdateFeedPostCommentService.build(session)
        with pytest.raises(FeedPostCommentNotFoundError):
            await svc.execute(
                feed_post_id=post.id,
                comment_id=999999,
                actor_user_id=user.id,
                text='nope',
            )


@pytest.mark.asyncio
async def test_update_feed_post_comment_mismatch(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=891002)
    post = await _create_post(user.id)
    comment = await _create_comment(post_id=post.id, user_id=user.id)
    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = UpdateFeedPostCommentService.build(session)
        with pytest.raises(FeedPostCommentMismatchError):
            await svc.execute(
                feed_post_id=post.id + 999,
                comment_id=comment.id,
                actor_user_id=user.id,
                text='wrong post',
            )


@pytest.mark.asyncio
async def test_update_feed_post_comment_forbidden(async_client: AsyncClient) -> None:
    owner = await _create_user(telegram_user_id=891003)
    other = await _create_user(telegram_user_id=891004)
    post = await _create_post(owner.id)
    comment = await _create_comment(post_id=post.id, user_id=owner.id)
    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = UpdateFeedPostCommentService.build(session)
        with pytest.raises(FeedPostCommentForbiddenError):
            await svc.execute(
                feed_post_id=post.id,
                comment_id=comment.id,
                actor_user_id=other.id,
                text='hack',
            )


@pytest.mark.asyncio
async def test_update_feed_post_comment_invalid_reaction_token(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=891005)
    post = await _create_post(user.id)
    comment = await _create_comment(post_id=post.id, user_id=user.id)
    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = UpdateFeedPostCommentService.build(session)
        with pytest.raises(FeedPostCommentValidationError):
            await svc.execute(
                feed_post_id=post.id,
                comment_id=comment.id,
                actor_user_id=user.id,
                text='⟦@unknown_slug⟧',
            )


@pytest.mark.asyncio
async def test_update_feed_post_comment_success(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=891006)
    post = await _create_post(user.id)
    comment = await _create_comment(post_id=post.id, user_id=user.id, text='before')
    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = UpdateFeedPostCommentService.build(session)
        updated = await svc.execute(
            feed_post_id=post.id,
            comment_id=comment.id,
            actor_user_id=user.id,
            text='  after  ',
        )
        assert updated.text == 'after'


@pytest.mark.asyncio
async def test_delete_feed_post_comment_errors(async_client: AsyncClient) -> None:
    owner = await _create_user(telegram_user_id=891007)
    other = await _create_user(telegram_user_id=891008)
    post = await _create_post(owner.id)
    comment = await _create_comment(post_id=post.id, user_id=owner.id)
    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = DeleteFeedPostCommentService.build(session)
        with pytest.raises(DeleteFeedPostCommentNotFoundError):
            await svc.execute(
                feed_post_id=post.id,
                comment_id=999999,
                actor_user_id=owner.id,
            )
        with pytest.raises(DeleteFeedPostCommentMismatchError):
            await svc.execute(
                feed_post_id=post.id + 1,
                comment_id=comment.id,
                actor_user_id=owner.id,
            )
        with pytest.raises(DeleteFeedPostCommentForbiddenError):
            await svc.execute(
                feed_post_id=post.id,
                comment_id=comment.id,
                actor_user_id=other.id,
            )


@pytest.mark.asyncio
async def test_delete_feed_post_comment_success(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=891009)
    post = await _create_post(user.id)
    comment = await _create_comment(post_id=post.id, user_id=user.id)
    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = DeleteFeedPostCommentService.build(session)
        await svc.execute(
            feed_post_id=post.id,
            comment_id=comment.id,
            actor_user_id=user.id,
        )
        gone = (
            await session.execute(
                select(FeedPostComment).where(FeedPostComment.id == comment.id)
            )
        ).scalar_one_or_none()
        assert gone is None
