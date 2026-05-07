"""Notify card or comment owner when someone adds a reaction (Telegram DM)."""

from __future__ import annotations

import html
import logging
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select

from core.database import get_session_factory
from models.movie_card import MovieCard
from models.movie_card_comment import MovieCardComment
from models.reaction_target_kind import ReactionTargetKind
from models.reaction_type import ReactionType
from models.user import User
from services.telegram.engagement_delivery import deliver_engagement_html_message
from services.telegram.mini_app_link import telegram_mini_app_card_url

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
class NotifyTelegramReactionAddedService:
    """Sends a Telegram DM when a user adds (not removes) a reaction on a card or comment."""

    async def execute(
        self,
        *,
        actor_user_id: UUID,
        target_kind: ReactionTargetKind,
        target_id: int,
        reaction_type_id: int,
    ) -> None:
        factory = get_session_factory()
        async with factory() as session:
            owner_id: UUID | None = None
            card_id_for_link: int | None = None

            if target_kind == ReactionTargetKind.MOVIE_CARD:
                row = await session.execute(
                    select(MovieCard.user_id).where(MovieCard.id == target_id)
                )
                owner_id = row.scalar_one_or_none()
                card_id_for_link = target_id
            elif target_kind == ReactionTargetKind.MOVIE_CARD_COMMENT:
                row = (
                    await session.execute(
                        select(MovieCardComment.user_id, MovieCardComment.movie_card_id).where(
                            MovieCardComment.id == target_id
                        )
                    )
                ).one_or_none()
                if row is None:
                    return
                owner_id = row[0]
                card_id_for_link = row[1]
            else:
                return

            if owner_id is None or owner_id == actor_user_id or card_id_for_link is None:
                return

            rt = await session.get(ReactionType, reaction_type_id)
            raw_label = (rt.label.strip() if rt and rt.label else '') or ''
            reaction_label = raw_label if raw_label else 'реакция'

            actor = await session.get(User, actor_user_id)
            recipient = await session.get(User, owner_id)
            if actor is None or recipient is None:
                return

            actor_safe = html.escape(_format_actor_display(actor))
            reaction_safe = html.escape(reaction_label)
            target_phrase = (
                '🎬 вашу карточку'
                if target_kind == ReactionTargetKind.MOVIE_CARD
                else '💭 ваш комментарий'
            )
            header = (
                '🎬 ✨ Реакция на карточку'
                if target_kind == ReactionTargetKind.MOVIE_CARD
                else '💬 ✨ Реакция на комментарий'
            )

            url = telegram_mini_app_card_url(card_id_for_link)
            link_html = (
                f'🔗 <a href="{html.escape(url, quote=True)}">Открыть в Filmony</a>'
                if url
                else '📱 Откройте Mini App из Telegram'
            )
            body_lines = [
                f'🔔 <b>Filmony</b> · уведомление',
                '',
                header,
                '',
                f'👤 <b>{actor_safe}</b>',
                f'❤️ На {target_phrase}: <b>{reaction_safe}</b>',
                '',
                link_html,
            ]
            body = '\n'.join(body_lines)

            await deliver_engagement_html_message(recipient.telegram_user_id, body)

    @classmethod
    def build(cls) -> Self:
        return cls()


async def run_notify_reaction_added_safe(
    *,
    actor_user_id: UUID,
    target_kind: ReactionTargetKind,
    target_id: int,
    reaction_type_id: int,
) -> None:
    try:
        await NotifyTelegramReactionAddedService.build().execute(
            actor_user_id=actor_user_id,
            target_kind=target_kind,
            target_id=target_id,
            reaction_type_id=reaction_type_id,
        )
    except Exception:
        logger.exception(
            'notify reaction telegram failed kind=%s target_id=%s',
            target_kind.value,
            target_id,
        )
