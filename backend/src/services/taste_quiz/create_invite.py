from __future__ import annotations

import datetime as dt
import secrets
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from models.taste_quiz_invite import TasteQuizInvite
from models.user import User
from services.taste_quiz.constants import INVITE_EXPIRY_DAYS
from services.telegram.mini_app_link import telegram_mini_app_taste_quiz_url


def _format_user_display(user: User) -> str:
    if user.display_name and user.display_name.strip():
        return user.display_name.strip()
    parts = [user.first_name or '', user.last_name or '']
    joined = ' '.join(p for p in parts if p).strip()
    if joined:
        return joined
    return user.profile_slug or 'Пользователь'


@dataclass(frozen=True, slots=True)
class CreateTasteQuizInviteOutcome:
    invite_token: str
    share_url: str | None
    telegram_share_text: str


@dataclass
class CreateTasteQuizInviteService:
    """Creates an owner invite token with Telegram share payload."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        *,
        owner_user_id: UUID,
    ) -> CreateTasteQuizInviteOutcome:
        owner = await self._session.get(User, owner_user_id)
        if owner is None:
            raise ValueError('owner not found')

        token = secrets.token_urlsafe(24)
        expires_at = dt.datetime.now(tz=dt.UTC) + dt.timedelta(days=INVITE_EXPIRY_DAYS)
        invite = TasteQuizInvite(
            owner_user_id=owner_user_id,
            token=token,
            expires_at=expires_at,
        )
        self._session.add(invite)
        await self._session.commit()

        share_url = telegram_mini_app_taste_quiz_url(token)
        owner_name = _format_user_display(owner)
        if share_url:
            telegram_share_text = (
                f'{owner_name} приглашает угадать его вкус в Filmony 🎬\n'
                f'Открой квиз: {share_url}'
            )
        else:
            telegram_share_text = f'{owner_name} приглашает угадать его вкус в Filmony 🎬'

        return CreateTasteQuizInviteOutcome(
            invite_token=token,
            share_url=share_url,
            telegram_share_text=telegram_share_text,
        )
