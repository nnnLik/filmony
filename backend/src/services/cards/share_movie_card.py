"""Валидация «поделиться карточкой» только с подписчиками (followers)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_card import UserCard
from models.user_subscription import UserSubscription


@dataclass(frozen=True, slots=True)
class ShareMovieCardOutcome:
    recipient_ids: tuple[UUID, ...]


class MovieCardNotFoundForShareError(Exception):
    pass


class ShareMovieCardForbiddenError(Exception):
    pass


class ShareRecipientsEmptyError(Exception):
    pass


class ShareRecipientsTooManyError(Exception):
    pass


class ShareRecipientsNotFollowersError(Exception):
    pass


_MAX_RECIPIENTS = 100


class ShareMovieCardService:
    """Проверяет владельца карточки и что все адресаты — подписчики автора."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        actor_user_id: UUID,
        card_id: int,
        recipient_user_ids: list[UUID],
    ) -> ShareMovieCardOutcome:
        unique = tuple(dict.fromkeys(recipient_user_ids))
        if len(unique) == 0:
            raise ShareRecipientsEmptyError
        if len(unique) > _MAX_RECIPIENTS:
            raise ShareRecipientsTooManyError

        card = await self._session.get(UserCard, card_id)
        if card is None:
            raise MovieCardNotFoundForShareError()
        if card.user_id != actor_user_id:
            raise ShareMovieCardForbiddenError()

        stmt = select(UserSubscription.follower_user_id).where(
            UserSubscription.following_user_id == actor_user_id,
            UserSubscription.follower_user_id.in_(unique),
        )
        rows = (await self._session.execute(stmt)).scalars().all()
        found = set(rows)
        if len(found) != len(unique):
            raise ShareRecipientsNotFollowersError()

        return ShareMovieCardOutcome(recipient_ids=unique)
