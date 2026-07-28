from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.taste_quiz_enums import TasteQuizSessionStatus
from models.taste_quiz_invite import TasteQuizInvite
from models.taste_quiz_session import TasteQuizSession
from models.user import User
from models.user_subscription import UserSubscription
from services.taste_quiz.card_pool import count_meaningful_rated_cards
from services.taste_quiz.constants import GATE_MIN_RATED_CARDS


@dataclass(frozen=True, slots=True)
class CheckTasteQuizCanPlayOutcome:
    can_play: bool
    reason: str | None
    owner_rated_count: int
    requires_follow: bool
    guesser_follows_owner: bool
    active_session_id: UUID | None
    gate_min_rated_cards: int


@dataclass
class CheckTasteQuizCanPlayService:
    """Checks whether a guesser can start a taste quiz against an owner."""

    _session: AsyncSession

    class OwnerNotFoundError(Exception):
        pass

    class SelfPlayError(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        *,
        guesser_user_id: UUID,
        owner_user_id: UUID,
        invite_token: str | None = None,
    ) -> CheckTasteQuizCanPlayOutcome:
        if guesser_user_id == owner_user_id:
            raise self.SelfPlayError

        owner = await self._session.get(User, owner_user_id)
        if owner is None:
            raise self.OwnerNotFoundError

        owner_rated_count = await count_meaningful_rated_cards(self._session, owner_user_id)
        invite_valid = await self._is_valid_invite(
            owner_user_id=owner_user_id,
            invite_token=invite_token,
        )
        requires_follow = not invite_valid
        guesser_follows_owner = await self._guesser_follows_owner(
            guesser_user_id=guesser_user_id,
            owner_user_id=owner_user_id,
        )
        active_session_id = await self._active_session_id(
            guesser_user_id=guesser_user_id,
            owner_user_id=owner_user_id,
        )

        reason: str | None = None
        can_play = True
        if owner_rated_count < GATE_MIN_RATED_CARDS:
            can_play = False
            reason = 'owner_insufficient_cards'
        elif requires_follow and not guesser_follows_owner:
            can_play = False
            reason = 'not_following'
        elif active_session_id is not None:
            can_play = False
            reason = 'active_session_exists'

        return CheckTasteQuizCanPlayOutcome(
            can_play=can_play,
            reason=reason,
            owner_rated_count=owner_rated_count,
            requires_follow=requires_follow,
            guesser_follows_owner=guesser_follows_owner,
            active_session_id=active_session_id,
            gate_min_rated_cards=GATE_MIN_RATED_CARDS,
        )

    async def _is_valid_invite(
        self,
        *,
        owner_user_id: UUID,
        invite_token: str | None,
    ) -> bool:
        token = (invite_token or '').strip()
        if not token:
            return False
        now = dt.datetime.now(tz=dt.UTC)
        invite = (
            await self._session.execute(
                select(TasteQuizInvite).where(
                    TasteQuizInvite.token == token,
                    TasteQuizInvite.owner_user_id == owner_user_id,
                    TasteQuizInvite.expires_at > now,
                )
            )
        ).scalar_one_or_none()
        return invite is not None

    async def _guesser_follows_owner(
        self,
        *,
        guesser_user_id: UUID,
        owner_user_id: UUID,
    ) -> bool:
        row = (
            await self._session.execute(
                select(UserSubscription.id).where(
                    UserSubscription.follower_user_id == guesser_user_id,
                    UserSubscription.following_user_id == owner_user_id,
                )
            )
        ).scalar_one_or_none()
        return row is not None

    async def _active_session_id(
        self,
        *,
        guesser_user_id: UUID,
        owner_user_id: UUID,
    ) -> UUID | None:
        row = (
            await self._session.execute(
                select(TasteQuizSession.id).where(
                    TasteQuizSession.guesser_user_id == guesser_user_id,
                    TasteQuizSession.owner_user_id == owner_user_id,
                    TasteQuizSession.status == TasteQuizSessionStatus.ACTIVE,
                )
            )
        ).scalar_one_or_none()
        return row
