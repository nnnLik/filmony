from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.cards.feed_post_feed_mapping import feed_post_feed_item_to_response
from api.cards.schemas import (
    FeedPostFeedItemResponse,
    UserCardFeedItemResponse,
    UserCardFeedPageResponse,
)
from api.cards.user_card_feed_mapping import user_card_feed_item_to_response
from api.films.award_badges import film_award_badge_responses_by_film_ids
from api.films.schemas import FilmAwardBadgeResponse
from core.database import get_db
from deps.auth import CurrentUser
from services.cards.list_user_card_feed import FeedPostFeedItem, UserCardFeedItem
from services.feed.global_feed_head_broker import (
    get_global_feed_head_version,
    iter_global_feed_head_sse,
)
from services.feed.list_global_feed import GlobalFeedKind, ListGlobalFeedService

router = APIRouter(prefix='/feed', tags=['feed'])


def _global_feed_domain_to_response(
    page_items: list[UserCardFeedItem | FeedPostFeedItem],
    next_cursor: str | None,
    *,
    feed_head_version: int,
    award_badges_by_film_id: dict[int, list[FilmAwardBadgeResponse]],
) -> UserCardFeedPageResponse:
    out_items: list[UserCardFeedItemResponse | FeedPostFeedItemResponse] = []
    for item in page_items:
        if isinstance(item, FeedPostFeedItem):
            out_items.append(feed_post_feed_item_to_response(item))
            continue
        badges: list[FilmAwardBadgeResponse] = []
        if item.film_id is not None:
            badges = award_badges_by_film_id.get(item.film_id, [])
        out_items.append(
            user_card_feed_item_to_response(item, award_badges=badges),
        )
    return UserCardFeedPageResponse(
        items=out_items,
        next_cursor=next_cursor,
        feed_head_version=feed_head_version,
    )


@router.get(
    '/global',
    response_model=UserCardFeedPageResponse,
    summary='Глобальная лента (карточки и/или посты по времени)',
)
async def list_global_feed(
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    kind: GlobalFeedKind = Query(
        default='all',
        description='all — карточки и посты; posts — только посты; cards — только карточки',
    ),
    exclude_own: bool = Query(
        default=False,
        description='Исключить из выдачи посты и карточки текущего пользователя',
    ),
) -> UserCardFeedPageResponse:
    page = await ListGlobalFeedService.build(db).execute(
        viewer.id,
        kind,
        cursor,
        limit,
        exclude_own=exclude_own,
    )
    film_ids = [
        item.film_id
        for item in page.items
        if isinstance(item, UserCardFeedItem) and item.film_id is not None
    ]
    award_badges_by_film_id = await film_award_badge_responses_by_film_ids(db, film_ids)
    return _global_feed_domain_to_response(
        page.items,
        page.next_cursor,
        feed_head_version=get_global_feed_head_version(),
        award_badges_by_film_id=award_badges_by_film_id,
    )


@router.get(
    '/global/events',
    summary='SSE: версия головы глобальной ленты',
    response_class=StreamingResponse,
)
async def global_feed_events(_: CurrentUser) -> StreamingResponse:
    async def gen():
        async for chunk in iter_global_feed_head_sse():
            yield chunk

    return StreamingResponse(
        gen(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        },
    )
