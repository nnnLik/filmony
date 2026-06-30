from __future__ import annotations

import html
import logging
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import func, select

from core.database import disposable_async_session
from models.catalog_item import CatalogItem
from models.film import Film
from models.game import Game
from models.user import User
from models.user_card import UserCard
from models.watchlist_entry import WatchlistEntry
from services.cards.card_catalog_release_fields import universal_release_year_date
from services.telegram.engagement_delivery import deliver_engagement_html_message
from services.telegram.mini_app_link import html_card_deep_link_block
from services.telegram.send_bot_message import SendTelegramBotMessageService
from utils.http_url import normalize_absolute_http_url

logger = logging.getLogger(__name__)


def _format_actor_display(user: User) -> str:
    if user.display_name and user.display_name.strip():
        return user.display_name.strip()
    parts = [user.first_name or '', user.last_name or '']
    joined = ' '.join(p for p in parts if p).strip()
    if joined:
        return joined
    return user.profile_slug or 'Пользователь'


def _truncate_caption(raw: str, max_len: int = 1000) -> str:
    if len(raw) <= max_len:
        return raw
    return raw[: max_len - 1] + '…'


def _build_caption_html(
    *,
    actor: User,
    title: str,
    release_year: int | None,
    together_names: list[str],
    watch_note: str,
    planned_user_card_id: int,
) -> str:
    actor_safe = html.escape(_format_actor_display(actor))
    title_safe = html.escape((title or '').strip() or 'Без названия')
    year_part = f' ({release_year})' if release_year is not None else ''
    together_line = ''
    if together_names:
        names_safe = ', '.join(html.escape(n) for n in together_names)
        together_line = f'\n<b>Вместе:</b> {names_safe}'
    note_line = ''
    note = (watch_note or '').strip()
    if note:
        note_line = f'\n\n💬 {html.escape(note)}'
    deep = html_card_deep_link_block(
        planned_user_card_id,
        link_text='Открыть запланированную карточку',
    )
    return (
        f'🎬 <b>{actor_safe}</b> приглашает посмотреть вместе\n\n'
        f'<b>{title_safe}</b>{html.escape(year_part)}'
        f'{together_line}'
        f'{note_line}\n\n'
        f'{deep}'
    )


def _payload_stub(
    *,
    invited_user_id: UUID,
    actor_user_id: UUID,
    planned_user_card_id: int,
    title: str = 'Приглашение посмотреть вместе',
    body: str | None = None,
) -> dict:
    out: dict = {
        'user_id': invited_user_id,
        'title': title,
        'deeplink': f'filmony://card/{planned_user_card_id}',
        'metadata': {
            'actor_user_id': actor_user_id,
            'planned_user_card_id': planned_user_card_id,
        },
    }
    if body is not None:
        out['body'] = body
    return out


def _together_names(
    actor: User,
    partner_ids: list[UUID],
    users_by_id: dict[UUID, User],
) -> list[str]:
    names = [_format_actor_display(actor)]
    for pid in partner_ids:
        partner = users_by_id.get(pid)
        if partner is not None:
            names.append(_format_actor_display(partner))
    return names


async def _partner_ids_from_actor_entry(
    session,
    *,
    actor_user_id: UUID,
    card_id: str,
) -> list[UUID]:
    actor_entry = (
        await session.execute(
            select(WatchlistEntry).where(
                WatchlistEntry.user_id == actor_user_id,
                WatchlistEntry.card_id == card_id,
            )
        )
    ).scalar_one_or_none()
    if actor_entry is None:
        return []
    partner_ids: list[UUID] = []
    for raw in actor_entry.watch_with_user_ids or []:
        try:
            partner_ids.append(UUID(str(raw)))
        except (TypeError, ValueError):
            continue
    return partner_ids


async def _deliver_caption(
    *,
    chat_id: int,
    caption: str,
    poster_url: str | None,
    invited_user_id: UUID,
    actor_user_id: UUID,
    planned_user_card_id: int,
) -> dict:
    poster = normalize_absolute_http_url(poster_url)
    send_svc = SendTelegramBotMessageService.build()
    if poster is not None:
        try:
            await send_svc.send_photo(chat_id, poster, caption, parse_mode='HTML')
        except SendTelegramBotMessageService.TelegramChatUnavailable:
            logger.info(
                'watchlist invite skipped (no chat) recipient=%s card_id=%s',
                invited_user_id,
                planned_user_card_id,
            )
            return _payload_stub(
                invited_user_id=invited_user_id,
                actor_user_id=actor_user_id,
                planned_user_card_id=planned_user_card_id,
            )
        except SendTelegramBotMessageService.TelegramDeliveryFailed as exc:
            logger.warning(
                'watchlist invite sendPhoto failed, fallback to text card_id=%s err=%s',
                planned_user_card_id,
                exc,
            )
        else:
            return _payload_stub(
                invited_user_id=invited_user_id,
                actor_user_id=actor_user_id,
                planned_user_card_id=planned_user_card_id,
                body=caption,
            )

    await deliver_engagement_html_message(chat_id, caption)
    return _payload_stub(
        invited_user_id=invited_user_id,
        actor_user_id=actor_user_id,
        planned_user_card_id=planned_user_card_id,
        body=caption,
    )


@dataclass
class SendWatchlistInviteNotificationService:
    """Send a rich Telegram notification for watchlist invites."""

    @classmethod
    def build(cls) -> Self:
        return cls()

    async def execute(
        self,
        *,
        actor_user_id: UUID,
        invited_user_id: UUID,
        planned_user_card_id: int,
        card_id: str,
    ) -> dict:
        async with disposable_async_session() as session:
            actor = await session.get(User, actor_user_id)
            invited = await session.get(User, invited_user_id)
            if actor is None or invited is None or invited.telegram_user_id is None:
                return _payload_stub(
                    invited_user_id=invited_user_id,
                    actor_user_id=actor_user_id,
                    planned_user_card_id=planned_user_card_id,
                )

            film_pk = func.coalesce(UserCard.film_id, CatalogItem.film_id)
            card_row = (
                await session.execute(
                    select(UserCard, Film, Game)
                    .outerjoin(CatalogItem, CatalogItem.id == UserCard.catalog_item_id)
                    .outerjoin(Film, Film.id == film_pk)
                    .outerjoin(Game, Game.id == CatalogItem.game_id)
                    .where(UserCard.id == planned_user_card_id)
                )
            ).one_or_none()
            if card_row is None:
                return _payload_stub(
                    invited_user_id=invited_user_id,
                    actor_user_id=actor_user_id,
                    planned_user_card_id=planned_user_card_id,
                )
            card, film, game = card_row

            display_title = (card.display_title or '').strip()
            if not display_title and film is not None:
                display_title = (film.title or '').strip()
            if not display_title:
                display_title = 'Без названия'

            film_year = film.year if film is not None else None
            release_year, _release_date = universal_release_year_date(
                film_year=film_year,
                game_released=game.released if game is not None else None,
            )
            poster_url = (
                film.poster_url if film is not None and film.poster_url else card.display_cover_url
            )

            partner_ids = await _partner_ids_from_actor_entry(
                session,
                actor_user_id=actor_user_id,
                card_id=card_id,
            )
            users_by_id: dict[UUID, User] = {actor.id: actor}
            if partner_ids:
                for u in (
                    await session.execute(select(User).where(User.id.in_(partner_ids)))
                ).scalars():
                    users_by_id[u.id] = u

            caption = _truncate_caption(
                _build_caption_html(
                    actor=actor,
                    title=display_title,
                    release_year=release_year,
                    together_names=_together_names(actor, partner_ids, users_by_id),
                    watch_note=card.watch_note or '',
                    planned_user_card_id=planned_user_card_id,
                )
            )

            return await _deliver_caption(
                chat_id=int(invited.telegram_user_id),
                caption=caption,
                poster_url=poster_url,
                invited_user_id=invited_user_id,
                actor_user_id=actor_user_id,
                planned_user_card_id=planned_user_card_id,
            )
