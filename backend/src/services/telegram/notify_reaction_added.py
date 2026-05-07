"""Notify card or comment owner when someone adds a reaction (Telegram DM)."""

from __future__ import annotations

import html
import logging
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from core.database import disposable_async_session
from models.film import Film
from models.movie_card import MovieCard
from models.movie_card_comment import MovieCardComment
from models.reaction_target_kind import ReactionTargetKind
from models.user import User
from services.telegram.engagement_delivery import deliver_engagement_html_message
from services.telegram.mini_app_link import html_card_deep_link_block

logger = logging.getLogger(__name__)


def _format_film_title_html(film: Film) -> str:
    raw = (film.title or '').strip() or 'Фильм'
    title = html.escape(raw)
    if film.year is not None:
        return f'«{title}» ({int(film.year)})'
    return f'«{title}»'


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
        _ = reaction_type_id  # событие «поставили реакцию» без названия типа в тексте

        async with disposable_async_session() as session:
            owner_id: UUID | None = None
            card_id_for_link: int | None = None
            comment_text_for_dm: str | None = None
            film_for_dm: Film | None = None

            if target_kind == ReactionTargetKind.MOVIE_CARD:
                card = await session.get(MovieCard, target_id)
                if card is None:
                    return
                owner_id = card.user_id
                card_id_for_link = card.id
                film_for_dm = await session.get(Film, card.film_id)
            elif target_kind == ReactionTargetKind.MOVIE_CARD_COMMENT:
                comment = await session.get(MovieCardComment, target_id)
                if comment is None:
                    return
                owner_id = comment.user_id
                card_id_for_link = comment.movie_card_id
                comment_text_for_dm = comment.text
            else:
                return

            if owner_id is None or owner_id == actor_user_id or card_id_for_link is None:
                return

            actor = await session.get(User, actor_user_id)
            recipient = await session.get(User, owner_id)
            if actor is None or recipient is None:
                return

            actor_safe = html.escape(_format_actor_display(actor))
            deep_link = html_card_deep_link_block(card_id_for_link)

            if target_kind == ReactionTargetKind.MOVIE_CARD:
                film_hint = (
                    _format_film_title_html(film_for_dm) if film_for_dm is not None else '«…»'
                )
                body_lines = [
                    f'⭐ <b>{actor_safe}</b> отреагировал на вашу карточку фильма {film_hint}',
                    '',
                    deep_link,
                ]
            else:
                raw_snippet = (comment_text_for_dm or '').strip()
                snippet = html.escape(raw_snippet[:100] if raw_snippet else '…')
                body_lines = [
                    '⭐ Реакция на ваш комментарий',
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
