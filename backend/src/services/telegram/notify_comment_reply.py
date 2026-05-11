"""Notify parent comment author when someone replies (Telegram DM)."""

from __future__ import annotations

import html
import logging
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select

from core.database import disposable_async_session
from models.movie_card_comment import MovieCardComment
from models.user import User
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
class NotifyTelegramCommentReplyService:
    """Sends a Telegram DM when a user replies to another user's card comment."""

    async def execute(
        self,
        *,
        actor_user_id: UUID,
        card_id: int,
        parent_comment_id: int,
        reply_text: str,
    ) -> None:
        async with disposable_async_session() as session:
            parent_author_id = (
                await session.execute(
                    select(MovieCardComment.user_id).where(MovieCardComment.id == parent_comment_id)
                )
            ).scalar_one_or_none()
            if parent_author_id is None or parent_author_id == actor_user_id:
                return

            actor = await session.get(User, actor_user_id)
            recipient = await session.get(User, parent_author_id)
            if actor is None or recipient is None or recipient.telegram_user_id is None:
                return

            actor_safe = html.escape(_format_actor_display(actor))
            snippet = html.escape(reply_text.strip()[:160])
            deep_link = html_card_deep_link_block(card_id)
            body_lines = [
                '💬 Новый ответ',
                '',
                f'👤 <b>{actor_safe}</b>',
                f'📝 <i>«{snippet}»</i>',
                '',
                deep_link,
            ]
            body = '\n'.join(body_lines)

            await deliver_engagement_html_message(int(recipient.telegram_user_id), body)

    @classmethod
    def build(cls) -> Self:
        return cls()


async def run_notify_comment_reply_safe(
    *,
    actor_user_id: UUID,
    card_id: int,
    parent_comment_id: int,
    reply_text: str,
) -> None:
    try:
        await NotifyTelegramCommentReplyService.build().execute(
            actor_user_id=actor_user_id,
            card_id=card_id,
            parent_comment_id=parent_comment_id,
            reply_text=reply_text,
        )
    except Exception:
        logger.exception(
            'notify comment reply telegram failed card_id=%s parent=%s',
            card_id,
            parent_comment_id,
        )
