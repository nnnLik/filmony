"""List public rated user cards for one catalog item."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Self

from sqlalchemy import and_, desc, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.card_tag import CardTag
from models.user import User
from models.user_card import UserCard
from services.catalog.community_card_dto import (
    CommunityAuthorDTO,
    CommunityCardDTO,
    CommunityCardsPageDTO,
    decode_community_cursor,
    encode_community_cursor,
)


@dataclass
class ListCatalogCommunityCardsService:
    """Loads public rated cards linked to a catalog item for the community hub page."""

    _session: AsyncSession

    class InvalidCursor(Exception):
        pass

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        cursor: str | None,
        limit: int,
        *,
        catalog_item_id: int | None = None,
        film_id: int | None = None,
    ) -> CommunityCardsPageDTO:
        if catalog_item_id is None and film_id is None:
            raise ValueError('catalog_item_id or film_id is required')

        cap = max(1, min(limit, 50))
        cursor_ts = None
        cursor_id = None
        if cursor is not None and cursor.strip() != '':
            decoded = decode_community_cursor(cursor.strip())
            if decoded is None:
                raise self.InvalidCursor()
            cursor_ts, cursor_id = decoded

        if catalog_item_id is not None:
            anchor_filter = UserCard.catalog_item_id == catalog_item_id
            if film_id is not None:
                anchor_filter = or_(
                    UserCard.catalog_item_id == catalog_item_id,
                    and_(
                        UserCard.film_id == film_id,
                        UserCard.catalog_item_id.is_(None),
                    ),
                )
        else:
            anchor_filter = UserCard.film_id == film_id

        q = (
            select(UserCard, User)
            .join(User, User.id == UserCard.user_id)
            .where(anchor_filter)
            .where(UserCard.is_planned.is_(False))
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
            next_cursor = None
        else:
            page_rows = rows[:cap]
            last_card, _last_user = page_rows[-1]
            next_cursor = encode_community_cursor(last_card.updated_at, last_card.id)

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

        items: list[CommunityCardDTO] = []
        for card, author in page_rows:
            items.append(
                CommunityCardDTO(
                    id=int(card.id),
                    author=CommunityAuthorDTO(
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

        return CommunityCardsPageDTO(items=items, next_cursor=next_cursor)
