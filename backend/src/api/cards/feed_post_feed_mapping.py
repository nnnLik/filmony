"""Сериализация `FeedPostFeedItem` (доменная модель ленты) в HTTP-схему."""

from __future__ import annotations

from api.cards.schemas import (
    FeedPostCommentPreviewResponse,
    FeedPostFeedItemResponse,
    FeedPostReferencedCardResponse,
    MovieCardCommentAuthorResponse,
)
from api.reactions.schemas import reaction_target_summary_to_response
from services.cards.list_movie_card_feed import FeedPostFeedItem
from services.feed_posts.list_feed_post_comments import FeedPostCommentItem


def _feed_post_comment_preview_to_response(
    c: FeedPostCommentItem,
) -> FeedPostCommentPreviewResponse:
    return FeedPostCommentPreviewResponse(
        id=c.id,
        feed_post_id=c.feed_post_id,
        parent_comment_id=c.parent_comment_id,
        text=c.text,
        created_at=c.created_at,
        replies_count=c.replies_count,
        total_descendants_count=c.total_descendants_count,
        author=MovieCardCommentAuthorResponse(
            id=c.author.id,
            profile_slug=c.author.profile_slug,
            username=c.author.username,
            first_name=c.author.first_name,
            last_name=c.author.last_name,
            photo_url=c.author.photo_url,
            display_name=c.author.display_name,
        ),
        reactions=reaction_target_summary_to_response(c.reactions),
    )


def feed_post_feed_item_to_response(item: FeedPostFeedItem) -> FeedPostFeedItemResponse:
    ref = item.referenced_card
    return FeedPostFeedItemResponse(
        id=item.id,
        user_id=item.user_id,
        author=MovieCardCommentAuthorResponse(
            id=item.author.id,
            profile_slug=item.author.profile_slug,
            username=item.author.username,
            first_name=item.author.first_name,
            last_name=item.author.last_name,
            photo_url=item.author.photo_url,
            display_name=item.author.display_name,
        ),
        body=item.body,
        image_url=item.image_url,
        referenced_movie_card_id=item.referenced_movie_card_id,
        source_comment_id=item.source_comment_id,
        created_at=item.created_at,
        feed_source=item.feed_source,
        referenced_card=(
            FeedPostReferencedCardResponse(
                movie_card_id=ref.movie_card_id,
                film_title=ref.film_title,
                film_year=ref.film_year,
                film_poster_url=ref.film_poster_url,
                rating=ref.rating,
            )
            if ref is not None
            else None
        ),
        reactions=reaction_target_summary_to_response(item.reactions),
        comments_count=item.comments_count,
        comments_preview=[_feed_post_comment_preview_to_response(c) for c in item.comments_preview],
    )
