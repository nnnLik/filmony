from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.card_comment import CardComment
from models.feed_post import FeedPost
from models.user_card import UserCard
from services.feed_posts.validate_feed_post_body import (
    FeedPostBodyValidationError,
    validate_feed_post_body,
)


@dataclass(frozen=True, slots=True)
class CreateFeedPostInput:
    """Поля для создания поста ленты (plain text, опционально картинка и ссылка на карточку)."""

    body: str
    image_url: str | None
    referenced_user_card_id: int | None
    source_comment_id: int | None


@dataclass(frozen=True, slots=True)
class CreateFeedPostResult:
    post: FeedPost
    mentioned_user_ids: tuple[UUID, ...]


class FeedPostValidationError(Exception):
    """Общая ошибка валидации (пустой контент, несогласованные ссылки)."""


class ReferencedUserCardNotFoundError(Exception):
    pass


class SourceCommentNotFoundError(Exception):
    pass


class SourceCommentForbiddenError(Exception):
    pass


def _normalize_image_url(raw: str | None) -> str | None:
    if raw is None:
        return None
    s = raw.strip()
    if s == '':
        return None
    if len(s) > 2048:
        raise FeedPostValidationError('image_url max length is 2048')
    return s


class CreateFeedPostService:
    """Создаёт пост ленты: plain text и/или одна картинка, опционально ссылка на карточку фильма.

    Позволяет опубликовать пост «с нуля» или с привязкой к чужой/своей карточке. При указании
    ``source_comment_id`` пост привязывается к своему комментарию и карточке комментария;
    текст поста задаётся только полем ``body`` (без автоподстановки из комментария).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(session=session)

    async def execute(self, user_id: UUID, payload: CreateFeedPostInput) -> CreateFeedPostResult:
        body_raw = payload.body.strip() if payload.body else ''
        ref_card_id = payload.referenced_user_card_id
        source_comment_id = payload.source_comment_id

        if source_comment_id is not None:
            comment = (
                await self._session.execute(
                    select(CardComment).where(CardComment.id == source_comment_id)
                )
            ).scalar_one_or_none()
            if comment is None:
                raise SourceCommentNotFoundError
            if comment.user_id != user_id:
                raise SourceCommentForbiddenError
            if ref_card_id is not None and ref_card_id != comment.card_id:
                raise FeedPostValidationError('referenced user card id does not match comment card')
            ref_card_id = comment.card_id
            # Одна картинка на пост: при конвертации из комментария берём изображение комментария.
            image_url = _normalize_image_url(comment.image_url)
        else:
            image_url = _normalize_image_url(payload.image_url)

        if ref_card_id is not None:
            exists = (
                await self._session.execute(select(UserCard.id).where(UserCard.id == ref_card_id))
            ).scalar_one_or_none()
            if exists is None:
                raise ReferencedUserCardNotFoundError

        if body_raw == '' and image_url is None:
            raise FeedPostValidationError('body or image_url is required')

        body_final = ''
        mentioned_user_ids: tuple[UUID, ...] = ()
        if body_raw != '':
            try:
                body_final, mentioned_user_ids = await validate_feed_post_body(
                    body_raw, self._session, author_user_id=user_id
                )
            except FeedPostBodyValidationError as e:
                raise FeedPostValidationError(str(e)) from e

        entity = FeedPost(
            user_id=user_id,
            body=body_final,
            image_url=image_url,
            referenced_card_id=ref_card_id,
            source_comment_id=source_comment_id,
        )
        self._session.add(entity)
        await self._session.commit()
        await self._session.refresh(entity)
        return CreateFeedPostResult(post=entity, mentioned_user_ids=mentioned_user_ids)
