from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.cards.feed_post_feed_mapping import feed_post_feed_item_to_response
from api.cards.schemas import (
    FeedPostFeedItemResponse,
    MovieCardCommentAuthorResponse,
    MovieCardCommentResponse,
    MovieCardFeedItemResponse,
    MovieCardFeedPageResponse,
)
from api.reactions.schemas import reaction_target_summary_to_response
from core.database import get_db
from deps.auth import CurrentUser
from services.cards.list_movie_card_comments import MovieCardCommentItem
from services.cards.list_movie_card_feed import FeedPostFeedItem, MovieCardFeedItem
from services.feed.global_feed_head_broker import (
    get_global_feed_head_version,
    iter_global_feed_head_sse,
)
from services.feed.list_global_feed import GlobalFeedKind, ListGlobalFeedService

router = APIRouter(prefix='/feed', tags=['feed'])


def _comment_item_to_response(item: MovieCardCommentItem) -> MovieCardCommentResponse:
    return MovieCardCommentResponse(
        id=item.id,
        movie_card_id=item.movie_card_id,
        parent_comment_id=item.parent_comment_id,
        text=item.text,
        created_at=item.created_at,
        replies_count=item.replies_count,
        total_descendants_count=item.total_descendants_count,
        author=MovieCardCommentAuthorResponse(
            id=item.author.id,
            profile_slug=item.author.profile_slug,
            username=item.author.username,
            first_name=item.author.first_name,
            last_name=item.author.last_name,
            photo_url=item.author.photo_url,
            display_name=item.author.display_name,
        ),
        reactions=reaction_target_summary_to_response(item.reactions),
    )


def _global_feed_domain_to_response(
    page_items: list[MovieCardFeedItem | FeedPostFeedItem],
    next_cursor: str | None,
    *,
    feed_head_version: int,
) -> MovieCardFeedPageResponse:
    out_items: list[MovieCardFeedItemResponse | FeedPostFeedItemResponse] = []
    for item in page_items:
        if isinstance(item, FeedPostFeedItem):
            out_items.append(feed_post_feed_item_to_response(item))
            continue
        out_items.append(
            MovieCardFeedItemResponse(
                id=item.id,
                user_id=item.user_id,
                card_author=MovieCardCommentAuthorResponse(
                    id=item.card_author.id,
                    profile_slug=item.card_author.profile_slug,
                    username=item.card_author.username,
                    first_name=item.card_author.first_name,
                    last_name=item.card_author.last_name,
                    photo_url=item.card_author.photo_url,
                    display_name=item.card_author.display_name,
                ),
                film_id=item.film_id,
                film_kinopoisk_id=item.film_kinopoisk_id,
                film_genres=item.film_genres,
                film_title=item.film_title,
                film_year=item.film_year,
                film_poster_url=item.film_poster_url,
                rating=item.rating,
                company=item.company,
                mood_before=item.mood_before,
                mood_after=item.mood_after,
                custom_tags=item.custom_tags,
                watch_note=item.watch_note,
                feed_source=item.feed_source,
                reactions=reaction_target_summary_to_response(item.reactions),
                comments_count=item.comments_count,
                comments_preview=[_comment_item_to_response(c) for c in item.comments_preview],
                is_favorite=item.is_favorite,
            )
        )
    return MovieCardFeedPageResponse(
        items=out_items,
        next_cursor=next_cursor,
        feed_head_version=feed_head_version,
    )


@router.get(
    '/global',
    response_model=MovieCardFeedPageResponse,
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
) -> MovieCardFeedPageResponse:
    page = await ListGlobalFeedService.build(db).execute(
        viewer.id,
        kind,
        cursor,
        limit,
    )
    return _global_feed_domain_to_response(
        page.items,
        page.next_cursor,
        feed_head_version=get_global_feed_head_version(),
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
