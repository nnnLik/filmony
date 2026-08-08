"""Render personal digest Telegram teaser HTML (monthly and weekly)."""

from __future__ import annotations

import html
from dataclasses import dataclass
from typing import Self

from services.personal_digest.build_personal_digest import PersonalDigestDTO
from services.profile.build_monthly_recap import MonthlyRecap
from services.telegram.mini_app_link import (
    html_recap_deep_link_block,
    html_weekly_digest_deep_link_block,
)

_RU_MONTHS = (
    '',
    'январь',
    'февраль',
    'март',
    'апрель',
    'май',
    'июнь',
    'июль',
    'август',
    'сентябрь',
    'октябрь',
    'ноябрь',
    'декабрь',
)


def _films_word(count: int) -> str:
    if count % 10 == 1 and count % 100 != 11:
        return 'фильм'
    if 2 <= count % 10 <= 4 and not (12 <= count % 100 <= 14):
        return 'фильма'
    return 'фильмов'


def _format_vs_previous_delta(delta: int, *, prev_month: int) -> str:
    sign = '+' if delta > 0 else ''
    prev_label = _RU_MONTHS[prev_month] if 1 <= prev_month <= 12 else str(prev_month)
    return f'({sign}{delta} к {prev_label})'


@dataclass
class RenderPersonalDigestTelegramService:
    """Builds short personal digest teasers for Telegram (monthly and weekly HTML)."""

    @classmethod
    def build(cls) -> Self:
        return cls()

    def execute_weekly(self, digest: PersonalDigestDTO) -> str:
        lines = [f'📅 <b>Твоя неделя · {html.escape(digest.period_label)}</b>']
        lines.append(
            f'📽 {digest.total_rated} {_films_word(digest.total_rated)} · ср. {digest.average_rating}'
        )

        if digest.top_films:
            top = digest.top_films[0]
            lines.append(f'⭐ {html.escape(top.title)} — {top.rating}')

        if digest.top_director_name and digest.top_director_count > 0:
            lines.append(f'🎬 {html.escape(digest.top_director_name)}')
        elif digest.top_actor_name and digest.top_actor_count > 0:
            lines.append(f'🎭 {html.escape(digest.top_actor_name)}')

        gamification_bits: list[str] = []
        if digest.achievements_unlocked:
            gamification_bits.append(f'{len(digest.achievements_unlocked)} ачивки')
        if digest.collection_deltas:
            top_delta = digest.collection_deltas[0]
            gamification_bits.append(
                f'{html.escape(top_delta.title)} +{top_delta.films_rated_in_period}'
            )
        elif digest.new_stamps:
            gamification_bits.append(f'{len(digest.new_stamps)} штампа')
        elif digest.marathons_unlocked:
            gamification_bits.append(f'{len(digest.marathons_unlocked)} марафона')
        if gamification_bits:
            lines.append(f'🏆 {" · ".join(gamification_bits)}')

        if digest.streak_current > 0:
            lines.append(f'🔥 серия {digest.streak_current} дн.')
        elif digest.streak_best_in_period > 0:
            lines.append(f'🔥 серия {digest.streak_best_in_period} дн.')

        if digest.friends is not None and digest.friends.telegram_lines:
            lines.append('👥 Друзья за неделю')
            for item in digest.friends.telegram_lines:
                lines.append(
                    f'• {html.escape(item.author_display)} — {html.escape(item.line_text)}'
                )

        if digest.fun_facts:
            lines.append(html.escape(digest.fun_facts[0]))

        if digest.controversy is not None:
            lines.append(
                f'⚡ Сильнее всего разошлись с {html.escape(digest.controversy.friend_display)} '
                f'по «{html.escape(digest.controversy.film_title)}»'
            )

        lines.append('')
        lines.append(html_weekly_digest_deep_link_block(period_key=digest.period_key))
        return '\n'.join(lines)

    def execute(self, recap: MonthlyRecap) -> str:
        lines = [f'📊 <b>Итоги · {html.escape(recap.month_label)}</b>']
        lines.append(
            f'📽 {recap.total_rated} {_films_word(recap.total_rated)} · ср. {recap.average_rating}'
        )

        if recap.vs_previous_total_rated is not None:
            prev_month = recap.month - 1 if recap.month > 1 else 12
            lines.append(
                _format_vs_previous_delta(recap.vs_previous_total_rated, prev_month=prev_month)
            )

        if recap.top_director_name and recap.top_director_count > 0:
            lines.append(f'🎬 {html.escape(recap.top_director_name)} ({recap.top_director_count})')
        elif recap.top_actor_name and recap.top_actor_count > 0:
            lines.append(f'🎭 {html.escape(recap.top_actor_name)} ({recap.top_actor_count})')

        if recap.top_director_name and recap.top_actor_name and recap.top_actor_count > 0:
            lines.append(f'🎭 {html.escape(recap.top_actor_name)} ({recap.top_actor_count})')

        gamification_bits: list[str] = []
        if recap.achievements_unlocked:
            gamification_bits.append(f'{len(recap.achievements_unlocked)} ачивки')
        if recap.collection_deltas:
            top_delta = recap.collection_deltas[0]
            gamification_bits.append(
                f'{html.escape(top_delta.title)} +{top_delta.films_rated_in_period}'
            )
        elif recap.new_stamps:
            gamification_bits.append(f'{len(recap.new_stamps)} штампа')
        elif recap.marathons_unlocked:
            gamification_bits.append(f'{len(recap.marathons_unlocked)} марафона')
        if gamification_bits:
            lines.append(f'🏆 {" · ".join(gamification_bits)}')

        if recap.streak_best_in_period > 0:
            lines.append(f'🔥 лучшая серия {recap.streak_best_in_period} дн.')

        lines.append('')
        lines.append(html_recap_deep_link_block(year=recap.year, month=recap.month))
        return '\n'.join(lines)
