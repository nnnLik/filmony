"""Глобальная публичная лента: карточки и посты в одной хронологии по времени создания."""

from __future__ import annotations

import base64
import binascii
import datetime as dt
from dataclasses import dataclass
from typing import Literal, Self
from uuid import UUID

import orjson
from sqlalchemy import Integer, String, and_, or_, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import literal

from models.feed_post import FeedPost
from models.user_card import UserCard
from services.cards.list_movie_card_feed import (
    FeedPageEntry,
    ListMovieCardFeedService,
    MovieCardFeedPage,
)

GlobalFeedKind = Literal['all', 'posts', 'cards']

CURSOR_PREFIX = 'gf1.'


def _encode_cursor(sort_at: dt.datetime, kind_rank: int, eid: int) -> str:
    payload = {
        'v': 1,
        't': sort_at.isoformat(),
        'kr': kind_rank,
        'id': eid,
    }
    raw = orjson.dumps(payload)
    b64 = base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')
    return f'{CURSOR_PREFIX}{b64}'


def _decode_cursor(cursor: str | None) -> tuple[dt.datetime, int, int] | None:
    """Разбор keyset-курсора; один выход в конце для совместимости с PLR0911."""
    result: tuple[dt.datetime, int, int] | None = None
    if cursor and cursor.startswith(CURSOR_PREFIX):
        payload = cursor[len(CURSOR_PREFIX) :]
        pad = (-len(payload)) % 4
        if pad:
            payload += '=' * pad
        data: object | None = None
        try:
            raw = base64.urlsafe_b64decode(payload.encode('ascii'))
            data = orjson.loads(raw)
        except (ValueError, binascii.Error, orjson.JSONDecodeError):
            data = None
        if isinstance(data, dict) and int(data.get('v', 0)) == 1:
            ts = data.get('t')
            if isinstance(ts, str):
                try:
                    sort_at = dt.datetime.fromisoformat(ts.replace('Z', '+00:00'))
                    kr = int(data['kr'])
                    eid = int(data['id'])
                    result = (sort_at, kr, eid)
                except (KeyError, TypeError, ValueError):
                    pass
    return result


def _union_subquery(kind: GlobalFeedKind, viewer_user_id: UUID, *, exclude_own: bool):
    card_branch = select(
        literal('card', type_=String()).label('etype'),
        literal(0, type_=Integer()).label('kind_rank'),
        UserCard.id.label('eid'),
        UserCard.created_at.label('sort_at'),
    ).select_from(UserCard)
    if exclude_own:
        card_branch = card_branch.where(UserCard.user_id != viewer_user_id)
    post_branch = select(
        literal('post', type_=String()).label('etype'),
        literal(1, type_=Integer()).label('kind_rank'),
        FeedPost.id.label('eid'),
        FeedPost.created_at.label('sort_at'),
    ).select_from(FeedPost)
    if exclude_own:
        post_branch = post_branch.where(FeedPost.user_id != viewer_user_id)
    if kind == 'all':
        return union_all(card_branch, post_branch).subquery('u')
    if kind == 'cards':
        return card_branch.subquery('u')
    return post_branch.subquery('u')


@dataclass
class ListGlobalFeedService:
    """Отдаёт глобальную ленту: все публичные карточки и посты по времени, без соцграфа."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(
        self,
        viewer_user_id: UUID,
        kind: GlobalFeedKind,
        cursor: str | None,
        limit: int,
        *,
        exclude_own: bool = False,
    ) -> MovieCardFeedPage:
        cur = _decode_cursor(cursor)
        u = _union_subquery(kind, viewer_user_id, exclude_own=exclude_own)
        stmt = select(u.c.etype, u.c.kind_rank, u.c.eid, u.c.sort_at).select_from(u)
        if cur is not None:
            ca, kr, eid = cur
            stmt = stmt.where(
                or_(
                    u.c.sort_at < ca,
                    and_(u.c.sort_at == ca, u.c.kind_rank < kr),
                    and_(u.c.sort_at == ca, u.c.kind_rank == kr, u.c.eid < eid),
                )
            )
        stmt = stmt.order_by(u.c.sort_at.desc(), u.c.kind_rank.desc(), u.c.eid.desc()).limit(
            limit + 1
        )
        rows = (await self._session.execute(stmt)).all()
        has_more = len(rows) > limit
        page_rows = rows[:limit]

        ordered: list[tuple[Literal['card', 'post'], int]] = []
        for r in page_rows:
            et = str(r.etype)
            if et == 'card':
                ordered.append(('card', int(r.eid)))
            else:
                ordered.append(('post', int(r.eid)))

        hydrator = ListMovieCardFeedService(self._session)
        card_ids = [i for k, i in ordered if k == 'card']
        post_ids = [i for k, i in ordered if k == 'post']
        cards = await hydrator.hydrate_global_feed_movie_cards(viewer_user_id, card_ids)
        posts = await hydrator.hydrate_global_feed_posts(viewer_user_id, post_ids)
        byc = {c.id: c for c in cards}
        byp = {p.id: p for p in posts}

        items: list[FeedPageEntry] = []
        for kind_e, iid in ordered:
            if kind_e == 'card':
                if iid in byc:
                    items.append(byc[iid])
            elif iid in byp:
                items.append(byp[iid])

        next_cursor: str | None = None
        if has_more and page_rows:
            last = page_rows[-1]
            next_cursor = _encode_cursor(last.sort_at, int(last.kind_rank), int(last.eid))

        return MovieCardFeedPage(items=items, next_cursor=next_cursor)
