"""Map domain feed card items to API responses."""

from __future__ import annotations

from api.cards.feed_post_feed_mapping import (
    inline_mention_snippets_to_response,
    inline_user_card_snippets_to_response,
)
from api.cards.schemas import (
    UserCardCategorySnippet,
    UserCardCommentAuthorResponse,
    UserCardCommentResponse,
    UserCardFeedItemResponse,
)
from api.films.schemas import FilmAwardBadgeResponse
from api.reactions.schemas import reaction_target_summary_to_response
from services.cards.list_user_card_comments import UserCardCommentItem
from services.cards.list_user_card_feed import UserCardFeedItem


def comment_item_to_response(item: UserCardCommentItem) -> UserCardCommentResponse:
    return UserCardCommentResponse(
        id=item.id,
        movie_card_id=item.user_card_id,
        parent_comment_id=item.parent_comment_id,
        text=item.text,
        image_url=item.image_url,
        created_at=item.created_at,
        replies_count=item.replies_count,
        total_descendants_count=item.total_descendants_count,
        author=UserCardCommentAuthorResponse(
            id=item.author.id,
            profile_slug=item.author.profile_slug,
            username=item.author.username,
            first_name=item.author.first_name,
            last_name=item.author.last_name,
            photo_url=item.author.photo_url,
            display_name=item.author.display_name,
        ),
        reactions=reaction_target_summary_to_response(item.reactions),
        referenced_movie_cards=inline_user_card_snippets_to_response(
            item.referenced_inline_user_cards,
        ),
        referenced_mentions=inline_mention_snippets_to_response(item.referenced_mentions),
    )


def user_card_feed_item_to_response(
    item: UserCardFeedItem,
    *,
    award_badges: list[FilmAwardBadgeResponse] | None = None,
) -> UserCardFeedItemResponse:
    return UserCardFeedItemResponse(
        id=item.id,
        user_id=item.user_id,
        card_author=UserCardCommentAuthorResponse(
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
        film_primary_director_kinopoisk_id=item.film_primary_director_kinopoisk_id,
        film_primary_director_name=item.film_primary_director_name,
        film_title=item.film_title,
        film_year=item.film_year,
        release_year=item.release_year,
        release_date=item.release_date,
        film_poster_url=item.film_poster_url,
        catalog_item_id=item.catalog_item_id,
        provider=item.provider,
        external_id=item.external_id,
        display_title=item.display_title,
        display_cover_url=item.display_cover_url,
        display_summary=item.display_summary,
        rating=item.rating,
        company=item.company,
        mood_before=item.mood_before,
        mood_after=item.mood_after,
        custom_tags=item.custom_tags,
        watch_note=item.watch_note,
        category=UserCardCategorySnippet(id=item.category_id, name=item.category_name),
        feed_source=item.feed_source,
        reactions=reaction_target_summary_to_response(item.reactions),
        comments_count=item.comments_count,
        comments_preview=[comment_item_to_response(c) for c in item.comments_preview],
        is_favorite=item.is_favorite,
        is_planned=item.is_planned,
        audio_url=item.audio_url,
        award_badges=list(award_badges or ()),
    )
