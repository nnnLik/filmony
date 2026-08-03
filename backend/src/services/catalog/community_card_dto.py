"""Shared DTOs and cursor helpers for catalog community card lists."""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from uuid import UUID

_CURSOR_PREFIX = 'fc1'


@dataclass(frozen=True, slots=True)
class CommunityAuthorDTO:
    id: UUID
    profile_slug: str
    username: str | None
    first_name: str | None
    last_name: str | None
    photo_url: str | None
    display_name: str | None


@dataclass(frozen=True, slots=True)
class CommunityCardDTO:
    id: int
    author: CommunityAuthorDTO
    rating: float
    company: str
    mood_before: str
    mood_after: str
    watch_note: str
    custom_tags: list[str]
    updated_at: dt.datetime
    is_favorite: bool


@dataclass(frozen=True, slots=True)
class CommunityCardsPageDTO:
    items: list[CommunityCardDTO]
    next_cursor: str | None


def encode_community_cursor(updated_at: dt.datetime, card_id: int) -> str:
    us = int(updated_at.timestamp() * 1_000_000)
    return f'{_CURSOR_PREFIX}.{us}.{card_id}'


def decode_community_cursor(cursor: str) -> tuple[dt.datetime, int] | None:
    parts = cursor.split('.')
    if len(parts) != 3 or parts[0] != _CURSOR_PREFIX:
        return None
    try:
        us = int(parts[1], 10)
        cid = int(parts[2], 10)
    except ValueError:
        return None
    return dt.datetime.fromtimestamp(us / 1_000_000, tz=dt.UTC), cid
