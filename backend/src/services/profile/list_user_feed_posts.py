from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.feed_post import FeedPost
from models.film import Film
from models.movie_card import MovieCard
from models.user import User
from services.cards.list_movie_card_comments import MovieCardCommentAuthor
from services.cards.list_movie_card_feed import (
    FeedPostFeedItem,
    FeedPostReferencedCardSnippet,
    attach_feed_post_list_engagement,
)

_CURSOR_PREFIX = 'ufp1'


def _encode_cursor(created_at: dt.datetime, post_id: int) -> str:
    if created_at.tzinfo is None:
        created_at = created_at.replace(tzinfo=dt.UTC)
    us = int(created_at.timestamp() * 1_000_000)
    return f'{_CURSOR_PREFIX}.{us}.{post_id}'


def _decode_cursor(cursor: str) -> tuple[dt.datetime, int] | None:
    parts = cursor.split('.')
    if len(parts) != 3 or parts[0] != _CURSOR_PREFIX:
        return None
    try:
        us = int(parts[1], 10)
        pid = int(parts[2], 10)
    except ValueError:
        return None
    return dt.datetime.fromtimestamp(us / 1_000_000, tz=dt.UTC), pid


@dataclass(frozen=True, slots=True)
class UserFeedPostsPage:
    items: list[FeedPostFeedItem]
    next_cursor: str | None


@dataclass
class ListUserFeedPostsService:
    """Возвращает текстовые посты пользователя для вкладки «Посты» в профиле (новые сверху)."""

    _session: AsyncSession

    class InvalidCursor(Exception):
        pass

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        user_id: UUID,
        cursor: str | None,
        limit: int,
        viewer_user_id: UUID,
    ) -> UserFeedPostsPage:
        cursor_ts: dt.datetime | None = None
        cursor_id: int | None = None
        if cursor is not None and cursor.strip() != '':
            decoded = _decode_cursor(cursor.strip())
            if decoded is None:
                raise self.InvalidCursor
            cursor_ts, cursor_id = decoded

        cap = max(1, min(limit, 50))
        where_parts = [FeedPost.user_id == user_id]
        if cursor_ts is not None and cursor_id is not None:
            where_parts.append(
                or_(
                    FeedPost.created_at < cursor_ts,
                    and_(FeedPost.created_at == cursor_ts, FeedPost.id < cursor_id),
                )
            )

        stmt = (
            select(FeedPost, User)
            .join(User, User.id == FeedPost.user_id)
            .where(and_(*where_parts))
            .order_by(FeedPost.created_at.desc(), FeedPost.id.desc())
            .limit(cap + 1)
        )
        rows = (await self._session.execute(stmt)).all()
        has_more = len(rows) > cap
        slice_rows = rows[:cap] if has_more else rows

        if not slice_rows:
            return UserFeedPostsPage(items=[], next_cursor=None)

        ref_cids = [
            int(fp.referenced_movie_card_id) for fp, _ in slice_rows if fp.referenced_movie_card_id
        ]
        ref_by_cid: dict[int, tuple[MovieCard, Film]] = {}
        if ref_cids:
            rq = (
                select(MovieCard, Film)
                .join(Film, Film.id == MovieCard.film_id)
                .where(MovieCard.id.in_(ref_cids))
            )
            for card, film in (await self._session.execute(rq)).all():
                ref_by_cid[int(card.id)] = (card, film)

        items: list[FeedPostFeedItem] = []
        for fp, author_user in slice_rows:
            ref_snippet: FeedPostReferencedCardSnippet | None = None
            rid = fp.referenced_movie_card_id
            if rid is not None and int(rid) in ref_by_cid:
                mc, fl = ref_by_cid[int(rid)]
                ref_snippet = FeedPostReferencedCardSnippet(
                    movie_card_id=int(mc.id),
                    film_title=str(fl.title),
                    film_year=fl.year,
                    film_poster_url=fl.poster_url,
                    rating=float(mc.rating),
                )
            author = MovieCardCommentAuthor(
                id=author_user.id,
                profile_slug=author_user.profile_slug,
                username=author_user.username,
                first_name=author_user.first_name,
                last_name=author_user.last_name,
                photo_url=author_user.photo_url,
                display_name=author_user.display_name,
            )
            items.append(
                FeedPostFeedItem(
                    id=int(fp.id),
                    user_id=fp.user_id,
                    author=author,
                    body=fp.body or '',
                    image_url=fp.image_url,
                    referenced_movie_card_id=int(rid) if rid is not None else None,
                    source_comment_id=int(fp.source_comment_id)
                    if fp.source_comment_id is not None
                    else None,
                    created_at=fp.created_at,
                    feed_source='feed_posts',
                    referenced_card=ref_snippet,
                )
            )

        next_cursor: str | None = None
        if has_more and slice_rows:
            fp_last, _ = slice_rows[-1]
            next_cursor = _encode_cursor(fp_last.created_at, int(fp_last.id))

        enriched = await attach_feed_post_list_engagement(self._session, viewer_user_id, items)
        return UserFeedPostsPage(items=enriched, next_cursor=next_cursor)
