from __future__ import annotations

from enum import StrEnum


class ReactionTargetKind(StrEnum):
    """Значения `user_reaction.target_kind`; совпадают с API."""

    MOVIE_CARD = 'movie_card'
    MOVIE_CARD_COMMENT = 'movie_card_comment'
