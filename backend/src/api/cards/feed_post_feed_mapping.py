"""Сериализация `FeedPostFeedItem` (доменная модель ленты) в HTTP-схему."""

from __future__ import annotations

from api.cards.schemas import (
    FeedPostCommentPreviewResponse,
    FeedPostFeedItemResponse,
    FeedPostReferencedCardResponse,
    FeedPostSourceCommentSnippetResponse,
    MovieCardCommentAuthorResponse,
    ReferencedInlineMovieCardSnippetResponse,
    ReferencedMentionSnippetResponse,
)
from api.reactions.schemas import reaction_target_summary_to_response
from services.cards.inline_movie_card_ref_tokens import ReferencedInlineMovieCardSnippet
from services.cards.list_movie_card_feed import FeedPostFeedItem, FeedPostSourceCommentSnippet
from services.feed_posts.list_feed_post_comments import FeedPostCommentItem
from services.profile.batch_resolve_inline_mentions import ReferencedMentionSnippet


def inline_movie_card_snippets_to_response(
    seq: tuple[ReferencedInlineMovieCardSnippet, ...],
) -> list[ReferencedInlineMovieCardSnippetResponse]:
    return [
        ReferencedInlineMovieCardSnippetResponse(
            movie_card_id=s.movie_card_id,
            film_title=s.film_title,
            film_year=s.film_year,
        )
        for s in seq
    ]


def inline_mention_snippets_to_response(
    seq: tuple[ReferencedMentionSnippet, ...],
) -> list[ReferencedMentionSnippetResponse]:
    return [
        ReferencedMentionSnippetResponse(
            user_id=s.user_id,
            profile_slug=s.profile_slug,
            display_label=s.display_label,
            username=s.username,
            display_name=s.display_name,
            first_name=s.first_name,
            last_name=s.last_name,
        )
        for s in seq
    ]


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
        referenced_movie_cards=inline_movie_card_snippets_to_response(c.referenced_movie_cards),
        referenced_mentions=inline_mention_snippets_to_response(c.referenced_mentions),
    )


def _source_comment_snippet_to_response(
    s: FeedPostSourceCommentSnippet,
) -> FeedPostSourceCommentSnippetResponse:
    return FeedPostSourceCommentSnippetResponse(
        id=s.id,
        text=s.text,
        image_url=s.image_url,
        author=MovieCardCommentAuthorResponse(
            id=s.author.id,
            profile_slug=s.author.profile_slug,
            username=s.author.username,
            first_name=s.author.first_name,
            last_name=s.author.last_name,
            photo_url=s.author.photo_url,
            display_name=s.author.display_name,
        ),
        referenced_movie_cards=inline_movie_card_snippets_to_response(s.referenced_movie_cards),
        referenced_mentions=inline_mention_snippets_to_response(s.referenced_mentions),
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
        body_referenced_movie_cards=inline_movie_card_snippets_to_response(
            item.body_referenced_movie_cards
        ),
        body_referenced_mentions=inline_mention_snippets_to_response(item.body_referenced_mentions),
        source_comment=(
            _source_comment_snippet_to_response(item.source_comment)
            if item.source_comment is not None
            else None
        ),
    )
