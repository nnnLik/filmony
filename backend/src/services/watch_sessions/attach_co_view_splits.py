from __future__ import annotations

from dataclasses import replace
from uuid import UUID

from models.feed_post import FeedPost
from services.cards.list_user_card_feed import FeedPostFeedItem
from services.watch_sessions.list_co_view_splits import CoViewSplit, ListCoViewSplitsService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


async def attach_co_view_splits_to_feed_posts(
    session: AsyncSession,
    items: list[FeedPostFeedItem],
) -> list[FeedPostFeedItem]:
    if not items:
        return []

    post_ids = [it.id for it in items]
    rows = (
        await session.execute(
            select(FeedPost.id, FeedPost.watch_session_id).where(FeedPost.id.in_(post_ids))
        )
    ).all()
    session_by_post: dict[int, UUID] = {
        int(post_id): watch_session_id
        for post_id, watch_session_id in rows
        if watch_session_id is not None
    }
    if not session_by_post:
        return items

    splits_service = ListCoViewSplitsService.build(session)
    splits_by_post: dict[int, tuple[CoViewSplit, ...]] = {}
    for post_id, watch_session_id in session_by_post.items():
        splits_by_post[post_id] = await splits_service.execute(watch_session_id=watch_session_id)

    out: list[FeedPostFeedItem] = []
    for item in items:
        splits = splits_by_post.get(item.id)
        if not splits:
            out.append(item)
            continue
        out.append(replace(item, co_view_splits=splits))
    return out
