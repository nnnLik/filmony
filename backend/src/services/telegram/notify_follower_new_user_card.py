"""Telegram DM to a follower when the author publishes a new user card."""

from __future__ import annotations

import html
import logging
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from core.database import disposable_async_session
from models.film import Film
from models.user import User
from models.user_card import UserCard
from services.telegram.engagement_delivery import deliver_engagement_html_message
from services.telegram.mini_app_link import html_card_deep_link_block

logger = logging.getLogger(__name__)


def _format_actor_display(user: User) -> str:
    if user.display_name and user.display_name.strip():
        return user.display_name.strip()
    parts = [user.first_name or '', user.last_name or '']
    joined = ' '.join(p for p in parts if p).strip()
    if joined:
        return joined
    return user.profile_slug or 'Пользователь'


def _card_title_line_html(*, film: Film | None, card: UserCard) -> str:
    if film is not None:
        raw = (film.title or '').strip() or 'Фильм'
        title = html.escape(raw)
        if film.year is not None:
            return f'🎬 «{title}» ({int(film.year)})'
        return f'🎬 «{title}»'
    manual = (card.display_title or '').strip() or 'Карточка'
    return f'🎬 «{html.escape(manual)}»'


@dataclass
class NotifyTelegramFollowerNewUserCardService:
    """Sends a Telegram DM to one follower about a newly created card of ``actor_user_id``.

    Keeps follower discovery and batch scheduling in Celery tasks; each delivery verifies the card
    still belongs to the author and skips silently when Telegram is unavailable.
    """

    async def execute(
        self,
        *,
        actor_user_id: UUID,
        card_id: int,
        recipient_user_id: UUID,
    ) -> None:
        if recipient_user_id == actor_user_id:
            return
        async with disposable_async_session() as session:
            recipient = await session.get(User, recipient_user_id)
            if recipient is None or recipient.telegram_user_id is None:
                return

            actor = await session.get(User, actor_user_id)
            if actor is None:
                return

            card = await session.get(UserCard, card_id)
            if card is None or card.user_id != actor_user_id:
                return

            film = await session.get(Film, card.film_id) if card.film_id is not None else None
            actor_safe = html.escape(_format_actor_display(actor))
            title_line = _card_title_line_html(film=film, card=card)
            deep = html_card_deep_link_block(card_id)

            body = '\n'.join(
                [
                    f'📽 <b>{actor_safe}</b> опубликовал(а) новую карточку',
                    '',
                    title_line,
                    '',
                    deep,
                ]
            )
            await deliver_engagement_html_message(int(recipient.telegram_user_id), body)

    @classmethod
    def build(cls) -> Self:
        return cls()


async def run_notify_follower_new_user_card_safe(
    *,
    actor_user_id: UUID,
    card_id: int,
    recipient_user_id: UUID,
) -> None:
    try:
        await NotifyTelegramFollowerNewUserCardService.build().execute(
            actor_user_id=actor_user_id,
            card_id=card_id,
            recipient_user_id=recipient_user_id,
        )
    except Exception:
        logger.exception(
            'notify follower new user card failed card_id=%s recipient=%s',
            card_id,
            recipient_user_id,
        )
