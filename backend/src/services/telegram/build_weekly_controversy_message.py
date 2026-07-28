"""Render Telegram HTML for weekly controversy digest."""

from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Self

from services.controversy.compute_weekly_controversy import WeeklyControversyResult


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
        return (
            f'<b>Спорный тайтл недели</b>\n\n'
            f'«{title}» разделил ваш круг: оценки от {low:g} до {high:g} '
            f'(разброс {spread:g}, {count} человек).\n\n'
            f'Откройте Filmony, чтобы посмотреть мнения подписок.'
        )
