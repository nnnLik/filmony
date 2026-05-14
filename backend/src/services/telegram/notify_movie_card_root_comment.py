"""Уведомление владельца карточки о новом корневом комментарии (Telegram DM)."""

from __future__ import annotations

import html
import logging
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select

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


@dataclass
class NotifyTelegramMovieCardRootCommentService:
    """Отправляет DM владельцу карточки, когда оставлен корневой комментарий (не ответ)."""

    async def execute(
        self,
        *,
        actor_user_id: UUID,
        card_id: int,
        comment_text: str,
    ) -> None:
        async with disposable_async_session() as session:
            row = (
                await session.execute(
                    select(UserCard, Film)
                    .join(Film, Film.id == UserCard.film_id)
                    .where(UserCard.id == card_id)
                )
            ).one_or_none()
            if row is None:
                return
            card, film = row

            owner_id = card.user_id
            if owner_id == actor_user_id:
                return

            actor = await session.get(User, actor_user_id)
            recipient = await session.get(User, owner_id)
            if actor is None or recipient is None or recipient.telegram_user_id is None:
                return

            actor_safe = html.escape(_format_actor_display(actor))
            snippet = html.escape(comment_text.strip()[:160])
            title_safe = html.escape((film.title or '').strip() or 'Фильм')
            year_part = f' ({film.year})' if film.year is not None else ''
            deep_link = html_card_deep_link_block(card.id)

            body_lines = [
                '💬 Новый комментарий к вашей карточке',
                '',
                f'🎬 <b>{title_safe}</b>{html.escape(year_part)}',
                '',
                f'👤 <b>{actor_safe}</b>',
                f'📝 <i>«{snippet}»</i>',
                '',
                deep_link,
            ]
            body = '\n'.join(body_lines)

            await deliver_engagement_html_message(recipient.telegram_user_id, body)

    @classmethod
    def build(cls) -> Self:
        return cls()


async def run_notify_movie_card_root_comment_safe(
    *,
    actor_user_id: UUID,
    card_id: int,
    comment_text: str,
) -> None:
    try:
        await NotifyTelegramMovieCardRootCommentService.build().execute(
            actor_user_id=actor_user_id,
            card_id=card_id,
            comment_text=comment_text,
        )
    except Exception:
        logger.exception(
            'notify movie card root comment telegram failed card_id=%s',
            card_id,
        )
