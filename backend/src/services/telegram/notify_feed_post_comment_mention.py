"""Notify a user when they are @mentioned in a feed post comment (Telegram DM)."""

from __future__ import annotations

import html
import logging
import re
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from core.database import disposable_async_session
from models.feed_post_comment import FeedPostComment
from models.user import User
from services.telegram.engagement_delivery import deliver_engagement_html_message
from services.telegram.mini_app_link import html_feed_post_deep_link_block

logger = logging.getLogger(__name__)

_INLINE_TOKEN_RE = re.compile(r'⟦[^⟧]+⟧')


def _format_actor_display(user: User) -> str:
    if user.display_name and user.display_name.strip():
        return user.display_name.strip()
    parts = [user.first_name or '', user.last_name or '']
    joined = ' '.join(p for p in parts if p).strip()
    if joined:
        return joined
    return user.profile_slug or 'Пользователь'


def _snippet_from_comment_text(body: str, max_len: int = 160) -> str:
    raw = _INLINE_TOKEN_RE.sub(' ', body)
    raw = ' '.join(raw.split()).strip()
    if len(raw) <= max_len:
        return raw
    return raw[: max_len - 1] + '…'


@dataclass
class NotifyTelegramFeedPostCommentMentionService:
    """Sends a Telegram DM when a feed post comment @mentions the recipient."""

    async def execute(
        self,
        *,
        actor_user_id: UUID,
        feed_post_id: int,
        comment_id: int,
        recipient_user_id: UUID,
    ) -> None:
        async with disposable_async_session() as session:
            comment = await session.get(FeedPostComment, comment_id)
            if (
                comment is None
                or comment.user_id != actor_user_id
                or comment.feed_post_id != feed_post_id
            ):
                return

            actor = await session.get(User, actor_user_id)
            recipient = await session.get(User, recipient_user_id)
            if actor is None or recipient is None or recipient_user_id == actor_user_id:
                return

            chat_id = recipient.telegram_user_id
            if chat_id is None:
                return

            actor_safe = html.escape(_format_actor_display(actor))
            snippet = html.escape(_snippet_from_comment_text(comment.text))
            deep = html_feed_post_deep_link_block(feed_post_id)
            body_lines = [
                '📣 Вас упомянули в комментарии к посту',
                '',
                f'👤 <b>{actor_safe}</b>',
                f'📝 <i>«{snippet}»</i>' if snippet else '📝 <i>(без текста)</i>',
                '',
                deep,
            ]
            body = '\n'.join(body_lines)
            await deliver_engagement_html_message(int(chat_id), body)

    @classmethod
    def build(cls) -> Self:
        return cls()


async def run_notify_feed_post_comment_mention_safe(
    *,
    actor_user_id: UUID,
    feed_post_id: int,
    comment_id: int,
    recipient_user_id: UUID,
) -> None:
    try:
        await NotifyTelegramFeedPostCommentMentionService.build().execute(
            actor_user_id=actor_user_id,
            feed_post_id=feed_post_id,
            comment_id=comment_id,
            recipient_user_id=recipient_user_id,
        )
    except Exception:
        logger.exception(
            'notify feed post comment mention telegram failed post_id=%s comment_id=%s recipient=%s',
            feed_post_id,
            comment_id,
            recipient_user_id,
        )
