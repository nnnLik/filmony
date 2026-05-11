from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.movie_card import MovieCard
from models.movie_card_comment import MovieCardComment
from services.cards.comment_reaction_tokens import (
    CommentReactionTokenError,
    validate_comment_text_with_reaction_tokens,
)


@dataclass(frozen=True, slots=True)
class CreateMovieCardCommentInput:
    text: str
    parent_comment_id: int | None


class MovieCardNotFoundError(Exception):
    pass


class ParentCommentNotFoundError(Exception):
    pass


class ParentCommentMismatchError(Exception):
    pass


class MovieCardCommentValidationError(Exception):
    pass


async def _normalize_text(value: str, session: AsyncSession, author_user_id: UUID) -> str:
    try:
        return await validate_comment_text_with_reaction_tokens(
            value, session, author_user_id=author_user_id
        )
    except CommentReactionTokenError as e:
        raise MovieCardCommentValidationError(str(e)) from e


class CreateMovieCardCommentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        card_id: int,
        user_id: UUID,
        payload: CreateMovieCardCommentInput,
    ) -> MovieCardComment:
        text = await _normalize_text(payload.text, self._session, user_id)
        card = (
            await self._session.execute(select(MovieCard.id).where(MovieCard.id == card_id))
        ).scalar_one_or_none()
        if card is None:
            raise MovieCardNotFoundError()

        if payload.parent_comment_id is not None:
            parent_movie_card_id = (
                await self._session.execute(
                    select(MovieCardComment.movie_card_id).where(
                        MovieCardComment.id == payload.parent_comment_id
                    )
                )
            ).scalar_one_or_none()
            if parent_movie_card_id is None:
                raise ParentCommentNotFoundError()
            if parent_movie_card_id != card_id:
                raise ParentCommentMismatchError()

        comment = MovieCardComment(
            movie_card_id=card_id,
            user_id=user_id,
            parent_comment_id=payload.parent_comment_id,
            text=text,
        )
        self._session.add(comment)
        await self._session.commit()
        await self._session.refresh(comment)
        return comment
