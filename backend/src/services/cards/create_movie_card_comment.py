from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.movie_card import MovieCard
from models.movie_card_comment import MovieCardComment


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


def _normalize_text(value: str) -> str:
    text = value.strip()
    if text == '':
        raise MovieCardCommentValidationError('comment text must not be empty')
    if len(text) > 250:
        raise MovieCardCommentValidationError('comment text max length is 250')
    return text


class CreateMovieCardCommentService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        card_id: int,
        user_id: UUID,
        payload: CreateMovieCardCommentInput,
    ) -> MovieCardComment:
        text = _normalize_text(payload.text)
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
