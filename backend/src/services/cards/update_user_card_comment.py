from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.card_comment import CardComment
from services.cards.comment_reaction_tokens import (
    CommentReactionTokenError,
    validate_comment_text_with_reaction_tokens,
)
from services.cards.user_card_comment_image_url import normalize_user_card_comment_image_url


class UserCardCommentNotFoundError(Exception):
    pass


class UserCardCommentForbiddenError(Exception):
    pass


class UserCardCommentMismatchError(Exception):
    pass


class UserCardCommentValidationError(Exception):
    pass


@dataclass
class UpdateUserCardCommentService:
    """Updates text and optional image on a user card comment; author-only."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        card_id: int,
        comment_id: int,
        actor_user_id: UUID,
        text: str,
        image_url: str | None = None,
        *,
        clear_image: bool = False,
    ) -> CardComment:
        comment = (
            await self._session.execute(select(CardComment).where(CardComment.id == comment_id))
        ).scalar_one_or_none()
        if comment is None:
            raise UserCardCommentNotFoundError
        if comment.card_id != card_id:
            raise UserCardCommentMismatchError
        if comment.user_id != actor_user_id:
            raise UserCardCommentForbiddenError

        if clear_image:
            resolved_image: str | None = None
        elif image_url is not None:
            try:
                resolved_image = normalize_user_card_comment_image_url(image_url)
            except ValueError as exc:
                raise UserCardCommentValidationError(str(exc)) from exc
        else:
            resolved_image = comment.image_url

        text_stripped = text.strip()
        if text_stripped == '' and resolved_image is None:
            raise UserCardCommentValidationError('text or image_url is required')

        if text_stripped == '':
            text_final = ''
        else:
            try:
                text_final, _ = await validate_comment_text_with_reaction_tokens(
                    text, self._session, author_user_id=actor_user_id
                )
            except CommentReactionTokenError as exc:
                raise UserCardCommentValidationError(str(exc)) from exc

        comment.text = text_final
        comment.image_url = resolved_image
        await self._session.commit()
        await self._session.refresh(comment)
        return comment
