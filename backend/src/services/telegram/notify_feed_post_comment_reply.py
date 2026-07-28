"""Notify parent comment author when someone replies on a feed post (Telegram DM)."""

from __future__ import annotations

import html
import logging
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select

from core.database import disposable_async_session
from models.feed_post_comment import FeedPostComment
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
class NotifyTelegramFeedPostCommentReplyService:
    """Sends a Telegram DM when a user replies to another user's feed post comment."""

    async def execute(
        self,
        *,
        actor_user_id: UUID,
        feed_post_id: int,
        parent_comment_id: int,
        reply_text: str,
    ) -> None:
        async with disposable_async_session() as session:
            parent_row = (
                await session.execute(
                    select(FeedPostComment.user_id, FeedPostComment.feed_post_id).where(
                        FeedPostComment.id == parent_comment_id
                    )
                )
            ).one_or_none()
            if parent_row is None:
                return
            parent_author_id, parent_post_id = parent_row
            if parent_post_id != feed_post_id:
                return
            if parent_author_id == actor_user_id:
                return

            actor = await session.get(User, actor_user_id)
            recipient = await session.get(User, parent_author_id)
            if actor is None or recipient is None or recipient.telegram_user_id is None:
                return

            actor_safe = html.escape(_format_actor_display(actor))
            snippet = html.escape(reply_text.strip()[:160])
            deep_link = html_feed_post_deep_link_block(feed_post_id)
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


async def run_notify_feed_post_comment_reply_safe(
    *,
    actor_user_id: UUID,
    feed_post_id: int,
    parent_comment_id: int,
    reply_text: str,
) -> None:
    try:
        await NotifyTelegramFeedPostCommentReplyService.build().execute(
            actor_user_id=actor_user_id,
            feed_post_id=feed_post_id,
            parent_comment_id=parent_comment_id,
            reply_text=reply_text,
        )
    except Exception:
        logger.exception(
            'notify feed post comment reply telegram failed feed_post_id=%s parent=%s',
            feed_post_id,
            parent_comment_id,
        )
