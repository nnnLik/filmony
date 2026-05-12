"""Уведомление автора поста ленты о новом корневом комментарии (Telegram DM)."""

from __future__ import annotations

import html
import logging
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from core.database import disposable_async_session
from models.feed_post import FeedPost
from models.user import User
from services.telegram.engagement_delivery import deliver_engagement_html_message
from services.telegram.mini_app_link import html_feed_post_deep_link_block

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
class NotifyTelegramFeedPostRootCommentService:
    """Отправляет DM автору поста ленты при корневом комментарии (не ответ)."""

    async def execute(
        self,
        *,
        actor_user_id: UUID,
        feed_post_id: int,
        comment_text: str,
    ) -> None:
        async with disposable_async_session() as session:
            post = await session.get(FeedPost, feed_post_id)
            if post is None:
                return

            owner_id = post.user_id
            if owner_id == actor_user_id:
                return

            actor = await session.get(User, actor_user_id)
            recipient = await session.get(User, owner_id)
            if actor is None or recipient is None or recipient.telegram_user_id is None:
                return

            actor_safe = html.escape(_format_actor_display(actor))
            snippet = html.escape(comment_text.strip()[:160])
            post_preview = html.escape(post.body.strip()[:120] or 'Пост')
            deep_link = html_feed_post_deep_link_block(feed_post_id)

            body_lines = [
                '💬 Новый комментарий к вашему посту',
                '',
                f'📄 <b>{post_preview}</b>',
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


async def run_notify_feed_post_root_comment_safe(
    *,
    actor_user_id: UUID,
    feed_post_id: int,
    comment_text: str,
) -> None:
    try:
        await NotifyTelegramFeedPostRootCommentService.build().execute(
            actor_user_id=actor_user_id,
            feed_post_id=feed_post_id,
            comment_text=comment_text,
        )
    except Exception:
        logger.exception(
            'notify feed post root comment telegram failed feed_post_id=%s',
            feed_post_id,
        )
