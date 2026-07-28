"""Render Telegram HTML for weekly controversy digest."""

from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Self

from services.controversy.compute_weekly_controversy import WeeklyControversyResult
from services.telegram.mini_app_link import html_app_deep_link_block, html_card_deep_link_block

_LINK_TEXT = 'Посмотреть мнения подписок'


@dataclass
class BuildWeeklyControversyMessageService:
    """Formats the weekly controversial title summary for Telegram HTML delivery."""

    @classmethod
    def build(cls) -> Self:
        return cls()

    def execute(self, *, controversy: WeeklyControversyResult) -> str:
        title = html.escape(controversy.title)
        spread = controversy.spread
        low = controversy.min_rating
        high = controversy.max_rating
        count = controversy.rater_count

        if controversy.link_card_id is not None:
            deep = html_card_deep_link_block(
                controversy.link_card_id,
                link_text=_LINK_TEXT,
            )
        else:
            deep = html_app_deep_link_block(link_text=_LINK_TEXT)

        return '\n'.join(
            [
                '⚡ <b>Спорный тайтл недели</b>',
                '',
                f'🎬 «{title}»',
                '',
                f'📊 Оценки от {low:g} до {high:g} · разброс {spread:g} · {count} чел.',
                '',
                deep,
            ]
        )
