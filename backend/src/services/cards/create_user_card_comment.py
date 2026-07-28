from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.card_comment import CardComment
from models.user_card import UserCard
from services.cards.comment_reaction_tokens import (
    CommentReactionTokenError,
    validate_comment_text_with_reaction_tokens,
)
from services.cards.user_card_comment_image_url import normalize_user_card_comment_image_url


@dataclass(frozen=True, slots=True)
class CreateUserCardCommentInput:
    text: str
    parent_comment_id: int | None
    image_url: str | None = None


class UserCardNotFoundError(Exception):
    pass


class ParentCommentNotFoundError(Exception):
    pass


class ParentCommentMismatchError(Exception):
    pass


class UserCardCommentValidationError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class CreateUserCardCommentResult:
    comment: CardComment
    mentioned_user_ids: tuple[UUID, ...]


async def _normalize_text(
    value: str, session: AsyncSession, author_user_id: UUID
) -> tuple[str, tuple[UUID, ...]]:
    try:
        return await validate_comment_text_with_reaction_tokens(
            value, session, author_user_id=author_user_id
        )
    except CommentReactionTokenError as e:
        raise UserCardCommentValidationError(str(e)) from e


class CreateUserCardCommentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        card_id: int,
        user_id: UUID,
        payload: CreateUserCardCommentInput,
    ) -> CreateUserCardCommentResult:
        try:
            image_url = normalize_user_card_comment_image_url(payload.image_url)
        except ValueError as e:
            raise UserCardCommentValidationError(str(e)) from e

        text_stripped = payload.text.strip()
        if text_stripped == '' and image_url is None:
            raise UserCardCommentValidationError('text or image_url is required')

        if text_stripped == '':
            text_final = ''
            mentioned_user_ids: tuple[UUID, ...] = ()
        else:
            text_final, mentioned_user_ids = await _normalize_text(
                payload.text, self._session, user_id
            )

        card = (
            await self._session.execute(select(UserCard.id).where(UserCard.id == card_id))
        ).scalar_one_or_none()
        if card is None:
            raise UserCardNotFoundError()

        if payload.parent_comment_id is not None:
            parent_user_card_id = (
                await self._session.execute(
                    select(CardComment.card_id).where(CardComment.id == payload.parent_comment_id)
                )
            ).scalar_one_or_none()
            if parent_user_card_id is None:
                raise ParentCommentNotFoundError()
            if parent_user_card_id != card_id:
                raise ParentCommentMismatchError()

        comment = CardComment(
            card_id=card_id,
            user_id=user_id,
            parent_comment_id=payload.parent_comment_id,
            text=text_final,
            image_url=image_url,
        )
        self._session.add(comment)
        await self._session.commit()
        await self._session.refresh(comment)
        return CreateUserCardCommentResult(comment=comment, mentioned_user_ids=mentioned_user_ids)
