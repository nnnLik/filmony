from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.card_tag import CardTag
from models.user import User
from models.user_card import UserCard

_CURSOR_PREFIX = 'fc1'


@dataclass(frozen=True, slots=True)
class FilmCommunityAuthorDTO:
    id: UUID
    profile_slug: str
    username: str | None
    first_name: str | None
    last_name: str | None
    photo_url: str | None
    display_name: str | None


@dataclass(frozen=True, slots=True)
class FilmCommunityCardDTO:
    id: int
    author: FilmCommunityAuthorDTO
    rating: float
    company: str
    mood_before: str
    mood_after: str
    watch_note: str
    custom_tags: list[str]
    updated_at: dt.datetime
    is_favorite: bool


@dataclass(frozen=True, slots=True)
class FilmCommunityCardsPageDTO:
    items: list[FilmCommunityCardDTO]
    next_cursor: str | None


def _encode_cursor(updated_at: dt.datetime, card_id: int) -> str:
    us = int(updated_at.timestamp() * 1_000_000)
    return f'{_CURSOR_PREFIX}.{us}.{card_id}'


def _decode_cursor(cursor: str) -> tuple[dt.datetime, int] | None:
    parts = cursor.split('.')
    if len(parts) != 3 or parts[0] != _CURSOR_PREFIX:
        return None
    try:
        us = int(parts[1], 10)
        cid = int(parts[2], 10)
    except ValueError:
        return None
    return dt.datetime.fromtimestamp(us / 1_000_000, tz=dt.UTC), cid


@dataclass
class ListFilmCommunityCardsService:
    """Loads public movie cards for a catalog film (who rated it, notes, tags).

    Powers the catalog film page so viewers can read community scores and notes before adding their own card.
    """

    _session: AsyncSession

    class InvalidCursor(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(session)

    async def execute(
        self, film_id: int, cursor: str | None, limit: int
    ) -> FilmCommunityCardsPageDTO:
        cap = max(1, min(limit, 50))
        cursor_ts: dt.datetime | None = None
        cursor_id: int | None = None
        if cursor is not None and cursor.strip() != '':
            decoded = _decode_cursor(cursor.strip())
            if decoded is None:
                raise self.InvalidCursor()
            cursor_ts, cursor_id = decoded

        q = (
            select(UserCard, User)
            .join(User, User.id == UserCard.user_id)
            .where(UserCard.film_id == film_id)
        )
        if cursor_ts is not None and cursor_id is not None:
            q = q.where(
                or_(
                    UserCard.updated_at < cursor_ts,
                    and_(UserCard.updated_at == cursor_ts, UserCard.id < cursor_id),
                )
            )
        q = q.order_by(desc(UserCard.updated_at), desc(UserCard.id)).limit(cap + 1)
        rows = (await self._session.execute(q)).all()
        if len(rows) <= cap:
            page_rows = rows
            next_cursor: str | None = None
        else:
            page_rows = rows[:cap]
            last_card, _last_user = page_rows[-1]
            next_cursor = _encode_cursor(last_card.updated_at, last_card.id)

        card_ids = [int(card.id) for card, _u in page_rows]
        tags_by_card: dict[int, list[str]] = {}
        if card_ids:
            tag_rows = (
                await self._session.execute(
                    select(CardTag.card_id, CardTag.tag)
                    .where(CardTag.card_id.in_(card_ids))
                    .order_by(CardTag.card_id, CardTag.tag)
                )
            ).all()
            for cid, tag in tag_rows:
                tags_by_card.setdefault(int(cid), []).append(tag)

        items: list[FilmCommunityCardDTO] = []
        for card, author in page_rows:
            items.append(
                FilmCommunityCardDTO(
                    id=int(card.id),
                    author=FilmCommunityAuthorDTO(
                        id=author.id,
                        profile_slug=author.profile_slug,
                        username=author.username,
                        first_name=author.first_name,
                        last_name=author.last_name,
                        photo_url=author.photo_url,
                        display_name=author.display_name,
                    ),
                    rating=float(card.rating),
                    company=card.company,
                    mood_before=card.mood_before,
                    mood_after=card.mood_after,
                    watch_note=card.watch_note or '',
                    custom_tags=tags_by_card.get(int(card.id), []),
                    updated_at=card.updated_at,
                    is_favorite=bool(card.is_favorite),
                )
            )

        return FilmCommunityCardsPageDTO(items=items, next_cursor=next_cursor)
