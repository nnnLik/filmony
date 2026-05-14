"""Notify card or comment owner when someone adds a reaction (Telegram DM)."""

from __future__ import annotations

import html
import logging
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.database import disposable_async_session
from models.card_comment import CardComment
from models.feed_post import FeedPost
from models.feed_post_comment import FeedPostComment
from models.film import Film
from models.reaction_target_kind import ReactionTargetKind
from models.user import User
from models.user_card import UserCard
from services.telegram.engagement_delivery import deliver_engagement_html_message
from services.telegram.mini_app_link import (
    html_card_deep_link_block,
    html_feed_post_deep_link_block,
)

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


@dataclass(frozen=True, slots=True)
class _ReactionDmTargetContext:
    owner_id: UUID
    card_id_for_link: int | None
    feed_post_id_for_link: int | None
    comment_text_for_dm: str | None
    film_for_dm: Film | None


async def _load_reaction_dm_target_context(
    session: AsyncSession,
    *,
    target_kind: ReactionTargetKind,
    target_id: int,
) -> _ReactionDmTargetContext | None:
    ctx: _ReactionDmTargetContext | None = None
    if target_kind == ReactionTargetKind.CARD:
        card = await session.get(UserCard, target_id)
        if card is not None:
            film_for_dm = await session.get(Film, card.film_id)
            ctx = _ReactionDmTargetContext(
                owner_id=card.user_id,
                card_id_for_link=card.id,
                feed_post_id_for_link=None,
                comment_text_for_dm=None,
                film_for_dm=film_for_dm,
            )
    elif target_kind == ReactionTargetKind.CARD_COMMENT:
        comment = await session.get(CardComment, target_id)
        if comment is not None:
            ctx = _ReactionDmTargetContext(
                owner_id=comment.user_id,
                card_id_for_link=comment.card_id,
                feed_post_id_for_link=None,
                comment_text_for_dm=comment.text,
                film_for_dm=None,
            )
    elif target_kind == ReactionTargetKind.FEED_POST_COMMENT:
        fp_comment = await session.get(FeedPostComment, target_id)
        if fp_comment is not None:
            ctx = _ReactionDmTargetContext(
                owner_id=fp_comment.user_id,
                card_id_for_link=None,
                feed_post_id_for_link=fp_comment.feed_post_id,
                comment_text_for_dm=fp_comment.text,
                film_for_dm=None,
            )
    elif target_kind == ReactionTargetKind.FEED_POST:
        fp_row = await session.get(FeedPost, target_id)
        if fp_row is not None:
            ctx = _ReactionDmTargetContext(
                owner_id=fp_row.user_id,
                card_id_for_link=None,
                feed_post_id_for_link=int(fp_row.id),
                comment_text_for_dm=fp_row.body or '',
                film_for_dm=None,
            )
    return ctx


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
            ctx = await _load_reaction_dm_target_context(
                session, target_kind=target_kind, target_id=target_id
            )
            if ctx is None:
                return
            if ctx.owner_id == actor_user_id:
                return
            if ctx.card_id_for_link is None and ctx.feed_post_id_for_link is None:
                return

            actor = await session.get(User, actor_user_id)
            recipient = await session.get(User, ctx.owner_id)
            if actor is None or recipient is None:
                return

            actor_safe = html.escape(_format_actor_display(actor))
            deep_link_card = (
                html_card_deep_link_block(ctx.card_id_for_link)
                if ctx.card_id_for_link is not None
                else ''
            )
            deep_link_post = (
                html_feed_post_deep_link_block(ctx.feed_post_id_for_link)
                if ctx.feed_post_id_for_link is not None
                else ''
            )

            if target_kind == ReactionTargetKind.CARD:
                film_hint = (
                    _format_film_title_html(ctx.film_for_dm)
                    if ctx.film_for_dm is not None
                    else '«…»'
                )
                body_lines = [
                    f'⭐ <b>{actor_safe}</b> отреагировал на вашу карточку фильма {film_hint}',
                    '',
                    deep_link_card,
                ]
            elif target_kind == ReactionTargetKind.CARD_COMMENT:
                raw_snippet = (ctx.comment_text_for_dm or '').strip()
                snippet = html.escape(raw_snippet[:100] if raw_snippet else '…')
                body_lines = [
                    '⭐ Реакция на ваш комментарий',
                    '',
                    f'👤 <b>{actor_safe}</b>',
                    f'📝 <i>«{snippet}»</i>',
                    '',
                    deep_link_card,
                ]
            elif target_kind == ReactionTargetKind.FEED_POST:
                raw_snippet = (ctx.comment_text_for_dm or '').strip()
                snippet = html.escape(raw_snippet[:100] if raw_snippet else '…')
                body_lines = [
                    '⭐ Реакция на ваш пост',
                    '',
                    f'👤 <b>{actor_safe}</b>',
                    f'📝 <i>«{snippet}»</i>',
                    '',
                    deep_link_post,
                ]
            else:
                raw_snippet = (ctx.comment_text_for_dm or '').strip()
                snippet = html.escape(raw_snippet[:100] if raw_snippet else '…')
                body_lines = [
                    '⭐ Реакция на ваш комментарий к посту',
                    '',
                    f'👤 <b>{actor_safe}</b>',
                    f'📝 <i>«{snippet}»</i>',
                    '',
                    deep_link_post,
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
