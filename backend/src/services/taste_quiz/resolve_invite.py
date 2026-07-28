from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.taste_quiz_invite import TasteQuizInvite
from models.user import User
from services.taste_quiz.card_pool import count_meaningful_rated_cards
from services.taste_quiz.check_can_play import CheckTasteQuizCanPlayService
from services.taste_quiz.constants import GATE_MIN_RATED_CARDS
from services.telegram.mini_app_link import telegram_mini_app_taste_quiz_url


@dataclass(frozen=True, slots=True)
class ResolveTasteQuizInviteOwnerSnippet:
    user_id: UUID
    profile_slug: str
    display_name: str | None
    avatar_url: str | None


@dataclass(frozen=True, slots=True)
class ResolveTasteQuizInviteOutcome:
    owner: ResolveTasteQuizInviteOwnerSnippet
    invite_token: str
    share_url: str | None
    can_play: bool
    reason: str | None
    owner_rated_count: int
    gate_min_rated_cards: int
    expired: bool


@dataclass
class ResolveTasteQuizInviteService:
    """Resolves an invite token for deep-link entry."""

    _session: AsyncSession

    class InviteNotFoundError(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        *,
        invite_token: str,
        guesser_user_id: UUID | None = None,
    ) -> ResolveTasteQuizInviteOutcome:
        token = invite_token.strip()
        invite = (
            await self._session.execute(
                select(TasteQuizInvite).where(TasteQuizInvite.token == token)
            )
        ).scalar_one_or_none()
        if invite is None:
            raise self.InviteNotFoundError

        now = dt.datetime.now(tz=dt.UTC)
        expired = invite.expires_at <= now
        owner = await self._session.get(User, invite.owner_user_id)
        if owner is None:
            raise self.InviteNotFoundError

        owner_rated_count = await count_meaningful_rated_cards(self._session, owner.id)
        can_play = owner_rated_count >= GATE_MIN_RATED_CARDS and not expired
        reason: str | None = None
        if expired:
            reason = 'invite_expired'
            can_play = False
        elif owner_rated_count < GATE_MIN_RATED_CARDS:
            reason = 'owner_insufficient_cards'
            can_play = False
        elif guesser_user_id is not None:
            check = await CheckTasteQuizCanPlayService.build(self._session).execute(
                guesser_user_id=guesser_user_id,
                owner_user_id=owner.id,
                invite_token=token,
            )
            if check.active_session_id is not None:
                can_play = False
                reason = 'active_session_exists'

        return ResolveTasteQuizInviteOutcome(
            owner=ResolveTasteQuizInviteOwnerSnippet(
                user_id=owner.id,
                profile_slug=owner.profile_slug,
                display_name=owner.display_name,
                avatar_url=owner.photo_url,
            ),
            invite_token=token,
            share_url=telegram_mini_app_taste_quiz_url(token),
            can_play=can_play,
            reason=reason,
            owner_rated_count=owner_rated_count,
            gate_min_rated_cards=GATE_MIN_RATED_CARDS,
            expired=expired,
        )
