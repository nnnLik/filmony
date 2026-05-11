"""Сериализация `FeedPostFeedItem` (доменная модель ленты) в HTTP-схему."""

from __future__ import annotations

from api.cards.schemas import (
    FeedPostFeedItemResponse,
    FeedPostReferencedCardResponse,
    MovieCardCommentAuthorResponse,
)
from services.cards.list_movie_card_feed import FeedPostFeedItem


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
    )
