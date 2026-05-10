"""Exports the current user's movie cards as CSV and delivers the file via Telegram DM."""

from __future__ import annotations

import csv
import datetime as dt
import io
import re
from dataclasses import dataclass
from typing import Self

from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from services.profile.list_user_movie_cards import ListUserMovieCardsService, MovieCardListItem
from services.telegram.send_bot_message import SendTelegramBotMessageService


def _safe_export_filename_slug(profile_slug: str) -> str:
    s = profile_slug.strip().lower()
    if len(s) > 80:
        s = s[:80]
    if not re.fullmatch(r'[a-z0-9_-]+', s):
        return 'profile'
    return s


def _movie_cards_to_csv_bytes(items: list[MovieCardListItem]) -> bytes:
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(
        [
            'card_id',
            'film_id',
            'kinopoisk_id',
            'title',
            'year',
            'genres',
            'rating',
            'company',
            'mood_before',
            'mood_after',
            'custom_tags',
            'watch_note',
            'poster_url',
            'updated_at',
        ]
    )
    for item in items:
        writer.writerow(
            [
                item.id,
                item.film_id,
                item.film_kinopoisk_id,
                item.film_title,
                '' if item.film_year is None else item.film_year,
                '|'.join(item.film_genres),
                item.rating,
                item.company,
                item.mood_before,
                item.mood_after,
                ';'.join(item.custom_tags),
                item.watch_note.replace('\r\n', '\n').replace('\n', ' '),
                item.film_poster_url or '',
                item.updated_at.isoformat(),
            ]
        )
    return buf.getvalue().encode('utf-8-sig')


@dataclass
class ExportMyMovieCardsCsvTelegramService:
    """Builds a UTF-8 CSV of all movie cards for one user and sends it as a Telegram document.

    Used from the profile screen so the user receives a portable dump in their chat with the bot.
    """

    _session: AsyncSession
    _telegram: SendTelegramBotMessageService

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session, _telegram=SendTelegramBotMessageService.build())

    async def execute(self, user: User) -> None:
        items = await ListUserMovieCardsService(self._session).list_all_for_user(user.id)
        csv_bytes = _movie_cards_to_csv_bytes(items)
        today = dt.datetime.now(dt.UTC).strftime('%Y%m%d')
        slug = _safe_export_filename_slug(user.profile_slug)
        filename = f'filmony-cards-{slug}-{today}.csv'
        await self._telegram.send_document(
            chat_id=int(user.telegram_user_id),
            document_bytes=csv_bytes,
            filename=filename,
            content_type='text/csv',
            caption='Экспорт карточек Filmony',
        )
