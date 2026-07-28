"""Calendar week and rolling rating window helpers for weekly controversy."""

from __future__ import annotations

import datetime as dt


def week_start_for_date(day: dt.date) -> dt.date:
    """Monday (ISO) calendar week start for ``day``."""
    return day - dt.timedelta(days=day.weekday())


def week_start_for_datetime(moment: dt.datetime) -> dt.date:
    """Monday week start in UTC for ``moment``."""
    day = moment.date() if moment.tzinfo is None else moment.astimezone(dt.UTC).date()
    return week_start_for_date(day)


def rating_window_start(moment: dt.datetime) -> dt.datetime:
    """Rolling seven-day lower bound (UTC-aware) for recent circle ratings."""
    moment = moment.replace(tzinfo=dt.UTC) if moment.tzinfo is None else moment.astimezone(dt.UTC)
    return moment - dt.timedelta(days=7)
