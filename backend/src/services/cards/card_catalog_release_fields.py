"""Derive universal ``release_year`` / ``release_date`` for user cards from Film or Game rows."""

from __future__ import annotations

import re
from datetime import date

_ISO_DATE_RE = re.compile(r'^(\d{4})-(\d{2})-(\d{2})$')


def split_game_released_iso(raw: str | None) -> tuple[str | None, int | None]:
    """Parse RAWG ``Game.released`` into ``(YYYY-MM-DD | None, year | None)``."""
    if raw is None:
        return None, None
    s = raw.strip()
    if not s:
        return None, None
    if 'T' in s:
        s = s.split('T', 1)[0]
    if len(s) >= 10:
        s = s[:10]
    m = _ISO_DATE_RE.match(s)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            date(y, mo, d)
        except ValueError:
            return None, None
        return s, y
    if len(s) == 4 and s.isdigit():
        return None, int(s)
    return None, None


def universal_release_year_date(
    *,
    film_year: int | None,
    game_released: str | None,
) -> tuple[int | None, str | None]:
    """Films use ``Film.year``; games use ``Game.released`` (ISO date). Film wins if both set."""
    if film_year is not None:
        return film_year, None
    iso, y = split_game_released_iso(game_released)
    return y, iso
