"""Tests for monthly recap Telegram nudge message rendering."""

from __future__ import annotations

from services.telegram.send_monthly_recap_nudge import (
    RecapNudgePreview,
    _render_recap_nudge_html,
)


def test_render_recap_nudge_without_preview() -> None:
    body = _render_recap_nudge_html(year=2026, month=7)
    assert 'Твои итоги за июль 2026' in body
    assert 'Зайди в Filmony' in body
    assert 'фильм' not in body.split('Зайди')[0]


def test_render_recap_nudge_with_preview_stats() -> None:
    body = _render_recap_nudge_html(
        year=2026,
        month=7,
        preview=RecapNudgePreview(
            total_rated=5,
            top_director_name='Дени Вильнёв',
            top_country='США',
        ),
    )
    assert '5 фильмов за месяц' in body
    assert 'Дени Вильнёв' in body
    assert 'США' not in body


def test_render_recap_nudge_preview_falls_back_to_country() -> None:
    body = _render_recap_nudge_html(
        year=2026,
        month=7,
        preview=RecapNudgePreview(
            total_rated=1,
            top_director_name=None,
            top_country='Япония',
        ),
    )
    assert '1 фильм за месяц' in body
    assert 'Япония' in body
