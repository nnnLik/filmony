from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.card_comment import CardComment


class UserCardCommentNotFoundError(Exception):
    pass


class UserCardCommentForbiddenError(Exception):
    pass


class UserCardCommentMismatchError(Exception):
    pass


@dataclass
class DeleteUserCardCommentService:
    """Hard-deletes a user card comment and reply subtree (DB CASCADE); author-only."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        card_id: int,
        comment_id: int,
        actor_user_id: UUID,
    ) -> None:
        comment = (
            await self._session.execute(select(CardComment).where(CardComment.id == comment_id))
        ).scalar_one_or_none()
        if comment is None:
            raise UserCardCommentNotFoundError
        if comment.card_id != card_id:
            raise UserCardCommentMismatchError
        if comment.user_id != actor_user_id:
            raise UserCardCommentForbiddenError

        await self._session.delete(comment)
        await self._session.commit()
