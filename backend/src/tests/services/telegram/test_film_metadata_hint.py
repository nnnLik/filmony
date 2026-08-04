"""Tests for concise film metadata hints in Telegram HTML."""

from __future__ import annotations

from services.telegram.film_metadata_hint import (
    format_film_meta_html_line,
    primary_country_label,
    truncate_label,
)


def test_primary_country_skips_overlong_label() -> None:
    assert primary_country_label(['Соединённые Штатs Америки очень длинное']) is None
    assert primary_country_label(['США']) == 'США'


def test_format_film_meta_html_line_joins_director_and_country() -> None:
    line = format_film_meta_html_line(
        director_name='Кристофер Нолан',
        countries=['США', 'Великобритания'],
    )
    assert line == '🎬 Кристофер Нолан · 🌍 США'


def test_format_film_meta_html_line_escapes_html() -> None:
    line = format_film_meta_html_line(
        director_name='A & B',
        countries=['США'],
    )
    assert '&amp;' in line


def test_truncate_label_shortens_long_text() -> None:
    assert truncate_label('x' * 50, max_len=10).endswith('…')
    assert len(truncate_label('x' * 50, max_len=10)) == 10
