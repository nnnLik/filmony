"""Render Telegram HTML for weekly controversy digest."""

from __future__ import annotations

import datetime as dt
import hashlib
import html
import random
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from services.controversy.compute_weekly_controversy import (
    ControversyPolarCard,
    WeeklyControversyBundle,
    WeeklyControversyResult,
)
from services.telegram.film_metadata_hint import format_film_meta_html_line
from services.telegram.mini_app_link import (
    controversy_deeplink_html_block,
    resolve_controversy_deeplink_url,
)

_LINK_TEXT = 'Посмотреть все мнения'
_INLINE_BUTTON_TEXT = 'Открыть в Filmony'
_VIEWER_MID_BAND = 1.5


@dataclass(frozen=True, slots=True)
class WeeklyControversyTelegramPayload:
    html: str
    reply_markup: dict[str, object] | None


def _deterministic_rng(*, recipient_user_id: UUID, week_start: dt.date) -> random.Random:
    seed_material = f'controversy-intro:{recipient_user_id}:{week_start.isoformat()}'.encode()
    seed_int = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], 'big')
    return random.Random(seed_int)


def _format_title_line(controversy: WeeklyControversyResult) -> str:
    title = html.escape(controversy.title)
    year = f' ({controversy.film_year})' if controversy.film_year is not None else ''
    return f'🎬 «{title}»{year}'


def _format_metadata_line(controversy: WeeklyControversyResult) -> str | None:
    return format_film_meta_html_line(
        director_name=controversy.primary_director_name,
        countries=(controversy.primary_country,) if controversy.primary_country else None,
    )


def _format_stats_line(controversy: WeeklyControversyResult) -> str:
    low = controversy.min_rating
    high = controversy.max_rating
    spread = controversy.spread
    count = controversy.rater_count
    count_word = 'оценка' if count == 1 else ('оценки' if 2 <= count <= 4 else 'оценок')
    avg_suffix = (
        f' (ср. {controversy.avg_rating:.1f})' if controversy.avg_rating is not None else ''
    )
    return (
        f'Ваш круг разошёлся: от {low:g} до {high:g}{avg_suffix} '
        f'· разброс {spread:g} · {count} {count_word}'
    )


def _format_polar_line(polar: ControversyPolarCard, *, emoji: str) -> str:
    author = html.escape(polar.author_display)
    return f'{emoji} {polar.rating:g}/10 — <b>{author}</b>'


def _viewer_position_label(controversy: WeeklyControversyResult) -> str:
    rating = controversy.viewer_rating
    if rating is None:
        return ''
    mid = (controversy.min_rating + controversy.max_rating) / 2
    if abs(rating - mid) <= _VIEWER_MID_BAND:
        return 'между полюсами круга'
    if rating - controversy.min_rating <= controversy.max_rating - rating:
        return 'ближе к низкой оценке'
    return 'ближе к высокой оценке'


def _format_viewer_line(controversy: WeeklyControversyResult) -> str | None:
    if controversy.viewer_rating is not None:
        position = _viewer_position_label(controversy)
        return f'Ваша оценка: <b>{controversy.viewer_rating:.0f}/10</b>' + (
            f' — {position}' if position else ''
        )
    return 'Вы ещё не оценивали — куда бы вы поставили?'


def _build_intro_candidates(controversy: WeeklyControversyResult) -> list[str]:
    candidates: list[str] = []
    if controversy.spread >= 6:
        candidates.append(
            f'🔥 Самый горячий тайтл у подписок — разброс <b>{controversy.spread:g}</b>:'
        )
    if controversy.rater_count >= 4:
        candidates.append(
            f'⚡ <b>{controversy.rater_count}</b> человек из вашего круга не смогли договориться:'
        )
    if controversy.avg_rating is not None:
        mid = (controversy.min_rating + controversy.max_rating) / 2
        if abs(controversy.avg_rating - mid) <= 1.0:
            candidates.append('🎭 Средняя оценка посередине, но мнения разлетелись в края:')
    candidates.append('⚡ <b>Спорный тайтл недели</b> в вашем круге:')
    return candidates


def _pick_intro(
    *,
    controversy: WeeklyControversyResult,
    recipient_user_id: UUID,
    week_start: dt.date,
) -> str:
    options = _build_intro_candidates(controversy)
    if len(options) == 1:
        return options[0]
    rng = _deterministic_rng(recipient_user_id=recipient_user_id, week_start=week_start)
    return rng.choice(options[:-1] if len(options) > 1 else options)


def _inline_button_markup(url: str | None) -> dict[str, object] | None:
    if url is None:
        return None
    return {
        'inline_keyboard': [
            [{'text': _INLINE_BUTTON_TEXT, 'url': url}],
        ],
    }


@dataclass
class BuildWeeklyControversyMessageService:
    """Formats the weekly controversial title summary for Telegram HTML delivery."""

    @classmethod
    def build(cls) -> Self:
        return cls()

    def execute(
        self,
        *,
        bundle: WeeklyControversyBundle,
        recipient_user_id: UUID,
        week_start: dt.date,
    ) -> WeeklyControversyTelegramPayload:
        primary = bundle.primary
        intro = _pick_intro(
            controversy=primary,
            recipient_user_id=recipient_user_id,
            week_start=week_start,
        )

        lines = [intro, '', _format_title_line(primary)]
        metadata_line = _format_metadata_line(primary)
        if metadata_line is not None:
            lines.append(metadata_line)
        lines.extend(['', _format_stats_line(primary)])

        if primary.polar_low is not None:
            lines.append('')
            lines.append(_format_polar_line(primary.polar_low, emoji='👎'))
        if primary.polar_high is not None:
            lines.append(_format_polar_line(primary.polar_high, emoji='👍'))

        viewer_line = _format_viewer_line(primary)
        if viewer_line:
            lines.extend(['', viewer_line])

        if bundle.runner_up is not None:
            runner_title = html.escape(bundle.runner_up.title)
            lines.extend(
                [
                    '',
                    f'Ещё спорный: «{runner_title}» — разброс {bundle.runner_up.spread:g}',
                ]
            )

        deep = controversy_deeplink_html_block(
            anchor_film_id=primary.anchor_film_id,
            link_card_id=primary.link_card_id,
            link_text=_LINK_TEXT,
        )
        lines.extend(['', deep])

        deeplink_url = resolve_controversy_deeplink_url(
            anchor_film_id=primary.anchor_film_id,
            link_card_id=primary.link_card_id,
        )
        return WeeklyControversyTelegramPayload(
            html='\n'.join(lines),
            reply_markup=_inline_button_markup(deeplink_url),
        )
