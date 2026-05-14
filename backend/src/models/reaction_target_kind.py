from __future__ import annotations

from enum import StrEnum


class ReactionTargetKind(StrEnum):
    """Values for `user_reaction.target_kind` and public API payloads.

    Member names describe the domain (`card`=user card).
    Stored / wire values stay `movie_card*` for DB and client compatibility."""

    CARD = 'movie_card'
    CARD_COMMENT = 'movie_card_comment'
    FEED_POST_COMMENT = 'feed_post_comment'
    FEED_POST = 'feed_post'
