"""ISO week bounds for personal weekly digest."""

from __future__ import annotations

import datetime as dt
import re

from services.controversy.week_bounds import week_start_for_date

_ISO_WEEK_KEY_RE = re.compile(r'^(\d{4})-W(\d{2})$')

_RU_MONTHS_SHORT = (
    '',
    'янв',
    'фев',
    'мар',
    'апр',
    'май',
    'июн',
    'июл',
    'авг',
    'сен',
    'окт',
    'ноя',
    'дек',
)


def iso_week_period_key(*, iso_year: int, iso_week: int) -> str:
    return f'{iso_year}-W{iso_week:02d}'


def parse_iso_week_period_key(period_key: str) -> tuple[int, int]:
    match = _ISO_WEEK_KEY_RE.match(period_key.strip())
    if match is None:
        raise ValueError(f'invalid ISO week period key: {period_key}')
    iso_year = int(match.group(1))
    iso_week = int(match.group(2))
    if iso_week < 1 or iso_week > 53:
        raise ValueError(f'invalid ISO week number: {iso_week}')
    return iso_year, iso_week


def week_bounds_for_iso_week(*, iso_year: int, iso_week: int) -> tuple[dt.datetime, dt.datetime]:
    week_start_date = dt.date.fromisocalendar(iso_year, iso_week, 1)
    start = dt.datetime.combine(week_start_date, dt.time.min, tzinfo=dt.UTC)
    end = start + dt.timedelta(days=7)
    return start, end


def previous_complete_iso_week(
    *,
    now: dt.datetime | None = None,
) -> tuple[str, int, int]:
    """Returns period key and ISO year/week for the week before the current calendar week."""
    if now is None:
        now = dt.datetime.now(tz=dt.UTC)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=dt.UTC)
    else:
        now = now.astimezone(dt.UTC)

    today = now.date()
    this_monday = week_start_for_date(today)
    prev_monday = this_monday - dt.timedelta(days=7)
    iso_year, iso_week, _ = prev_monday.isocalendar()
    return iso_week_period_key(iso_year=iso_year, iso_week=iso_week), iso_year, iso_week


def format_week_period_label(
    *,
    window_start: dt.datetime,
    window_end_exclusive: dt.datetime,
) -> str:
    start_date = window_start.date()
    end_date = (window_end_exclusive - dt.timedelta(seconds=1)).date()
    start_part = f'{start_date.day} {_RU_MONTHS_SHORT[start_date.month]}'
    end_part = f'{end_date.day} {_RU_MONTHS_SHORT[end_date.month]}'
    if start_date.year != end_date.year:
        start_part = f'{start_part} {start_date.year}'
        end_part = f'{end_part} {end_date.year}'
    return f'{start_part} – {end_part}'
