"""Отправка карточки фильма подписчику в Telegram (фото постера + подпись HTML)."""

from __future__ import annotations

import html
import logging
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select

from core.database import disposable_async_session
from models.card_enums import CardCompany, CardMoodAfter, CardMoodBefore
from models.card_tag import CardTag
from models.film import Film
from models.user import User
from models.user_card import UserCard
from services.telegram.mini_app_link import html_card_deep_link_block
from services.telegram.send_bot_message import SendTelegramBotMessageService
from utils.http_url import normalize_absolute_http_url

logger = logging.getLogger(__name__)

_COMPANY_RU: dict[str, str] = {
    CardCompany.alone.value: 'Один',
    CardCompany.partner.value: 'С партнёром',
    CardCompany.friends.value: 'С друзьями',
    CardCompany.family.value: 'С семьёй',
}

_MOOD_BEFORE_RU: dict[str, str] = {
    CardMoodBefore.relax.value: 'Расслабиться',
    CardMoodBefore.laugh.value: 'Поржать',
    CardMoodBefore.sad.value: 'Погрустить',
    CardMoodBefore.thrill.value: 'Напряжение',
}

_MOOD_AFTER_RU: dict[str, str] = {
    CardMoodAfter.laughed.value: 'Весёлый',
    CardMoodAfter.cried.value: 'Плакал',
    CardMoodAfter.enjoyed.value: 'Кайфанул',
    CardMoodAfter.tense.value: 'Уставший',
    CardMoodAfter.wasted_time.value: 'Зря потратил время',
}


def _format_actor_display(user: User) -> str:
    if user.display_name and user.display_name.strip():
        return user.display_name.strip()
    parts = [user.first_name or '', user.last_name or '']
    joined = ' '.join(p for p in parts if p).strip()
    if joined:
        return joined
    return user.profile_slug or 'Пользователь'


def _rating_line(value: float) -> str:
    if value == int(value):
        return str(int(value))
    return f'{value:.1f}'.replace('.', ',')


def _build_caption_html(
    *,
    actor: User,
    film_title: str,
    film_year: int | None,
    rating: float,
    company: str,
    mood_before: str,
    mood_after: str,
    custom_tags: list[str],
    card_id: int,
    share_comment: str = '',
) -> str:
    actor_safe = html.escape(_format_actor_display(actor))
    title_safe = html.escape((film_title or '').strip() or 'Фильм')
    year_part = f' ({film_year})' if film_year is not None else ''
    company_safe = html.escape(_COMPANY_RU.get(company, company))
    mb_safe = html.escape(_MOOD_BEFORE_RU.get(mood_before, mood_before))
    ma_safe = html.escape(_MOOD_AFTER_RU.get(mood_after, mood_after))
    rating_safe = html.escape(_rating_line(rating))

    mood_line = f'{company_safe} · {mb_safe} · {ma_safe}'
    tags_line = ''
    if custom_tags:
        escaped_tags = ', '.join(html.escape(t) for t in custom_tags)
        tags_line = f'\n<b>Свои теги:</b> {escaped_tags}'
    share_line = ''
    sc = (share_comment or '').strip()
    if sc:
        share_line = f'\n\n💬 <b>Комментарий:</b>\n{html.escape(sc)}'
    deep = html_card_deep_link_block(card_id)

    return (
        f'📽 <b>{actor_safe}</b> делится с вами карточкой\n\n'
        f'<b>{title_safe}</b>{html.escape(year_part)}\n'
        f'⭐️ Оценка: <b>{rating_safe}</b>\n'
        f'{mood_line}'
        f'{tags_line}'
        f'{share_line}\n\n'
        f'{deep}'
    )


def _truncate_caption(raw: str, max_len: int = 1000) -> str:
    if len(raw) <= max_len:
        return raw
    return raw[: max_len - 1] + '…'


@dataclass
class DeliverSharedMovieCardTelegramService:
    """Формирует DM с контекстом карточки; постер скачивается на сервере и уходит в Telegram как файл."""

    async def execute(
        self,
        *,
        actor_user_id: UUID,
        card_id: int,
        recipient_user_id: UUID,
        share_comment: str = '',
    ) -> None:
        async with disposable_async_session() as session:
            recipient = await session.get(User, recipient_user_id)
            if recipient is None or recipient.telegram_user_id is None:
                return

            actor = await session.get(User, actor_user_id)
            if actor is None:
                return

            row = (
                await session.execute(
                    select(UserCard, Film)
                    .join(Film, Film.id == UserCard.film_id)
                    .where(UserCard.id == card_id, UserCard.user_id == actor_user_id)
                )
            ).one_or_none()
            if row is None:
                return
            card, film = row

            tags = (
                (
                    await session.execute(
                        select(CardTag.tag)
                        .where(CardTag.card_id == card.id)
                        .order_by(CardTag.tag)
                    )
                )
                .scalars()
                .all()
            )

            caption = _truncate_caption(
                _build_caption_html(
                    actor=actor,
                    film_title=film.title,
                    film_year=film.year,
                    rating=float(card.rating),
                    company=card.company,
                    mood_before=card.mood_before,
                    mood_after=card.mood_after,
                    custom_tags=list(tags),
                    card_id=card.id,
                    share_comment=share_comment,
                )
            )

            chat_id = int(recipient.telegram_user_id)
            send_svc = SendTelegramBotMessageService.build()
            poster = normalize_absolute_http_url(film.poster_url)
            if poster is not None:
                try:
                    return await send_svc.send_photo(chat_id, poster, caption, parse_mode='HTML')
                except SendTelegramBotMessageService.TelegramChatUnavailable:
                    logger.info(
                        'shared card skipped (no chat) recipient=%s card_id=%s',
                        recipient_user_id,
                        card_id,
                    )
                    return
                except SendTelegramBotMessageService.TelegramDeliveryFailed as exc:
                    logger.warning(
                        'shared card sendPhoto failed, fallback to text card_id=%s err=%s',
                        card_id,
                        exc,
                    )

            try:
                await send_svc.execute(chat_id, caption, parse_mode='HTML')
            except SendTelegramBotMessageService.TelegramChatUnavailable:
                logger.info(
                    'shared card skipped (no chat) recipient=%s card_id=%s',
                    recipient_user_id,
                    card_id,
                )
            except SendTelegramBotMessageService.TelegramDeliveryFailed as exc:
                logger.warning('shared card text delivery failed card_id=%s err=%s', card_id, exc)

    @classmethod
    def build(cls) -> Self:
        return cls()


async def run_deliver_shared_movie_card_safe(
    *,
    actor_user_id: UUID,
    card_id: int,
    recipient_user_id: UUID,
    share_comment: str = '',
) -> None:
    try:
        await DeliverSharedMovieCardTelegramService.build().execute(
            actor_user_id=actor_user_id,
            card_id=card_id,
            recipient_user_id=recipient_user_id,
            share_comment=share_comment,
        )
    except Exception:
        logger.exception(
            'deliver shared movie card failed card_id=%s recipient=%s',
            card_id,
            recipient_user_id,
        )
