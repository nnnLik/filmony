"""Concise film director/country hints for Telegram HTML messages."""

from __future__ import annotations

import html

MAX_COUNTRY_LABEL = 28
MAX_DIRECTOR_LABEL = 40


def primary_country_label(countries: list[str] | tuple[str, ...] | None) -> str | None:
    if not countries:
        return None
    for raw in countries:
        if not isinstance(raw, str):
            continue
        label = raw.strip()
        if label and len(label) <= MAX_COUNTRY_LABEL:
            return label
    return None


def truncate_label(label: str, *, max_len: int) -> str:
    cleaned = label.strip()
    if len(cleaned) <= max_len:
        return cleaned
    return cleaned[: max_len - 1].rstrip() + '…'


def format_film_meta_html_line(
    *,
    director_name: str | None = None,
    countries: list[str] | tuple[str, ...] | None = None,
) -> str | None:
    """Single line like ``🎬 Nolan · 🌍 USA``; skips overlong country labels."""
    parts: list[str] = []
    director = (director_name or '').strip()
    if director:
        parts.append(f'🎬 {html.escape(truncate_label(director, max_len=MAX_DIRECTOR_LABEL))}')
    country = primary_country_label(countries)
    if country:
        parts.append(f'🌍 {html.escape(country)}')
    if not parts:
        return None
    return ' · '.join(parts)
