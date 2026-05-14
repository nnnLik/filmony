"""Политика self-react: см. `.cursor/features/movie-card-custom-reactions/feature.md` (разрешено по умолчанию)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import Select, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.card_comment import CardComment
from models.feed_post import FeedPost
from models.feed_post_comment import FeedPostComment
from models.reaction_target_kind import ReactionTargetKind
from models.reaction_type import ReactionType
from models.user_card import UserCard
from models.user_reaction import UserReaction

from .get_reaction_summaries_for_targets import GetReactionSummariesForTargetsService
from .types import ReactionTargetSummary

ALLOW_SELF_REACTION = True


@dataclass(frozen=True, slots=True)
class SetUserReactionInput:
    target_kind: ReactionTargetKind
    target_id: int
    reaction_type_id: int


@dataclass(frozen=True, slots=True)
class SetUserReactionOutcome:
    summary: ReactionTargetSummary
    reaction_was_added: bool


class ReactionTypeInvalidError(Exception):
    pass


class ReactionTargetNotFoundError(Exception):
    pass


class SelfReactionForbiddenError(Exception):
    pass


class SetOrToggleUserReactionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: UUID, payload: SetUserReactionInput) -> SetUserReactionOutcome:
        await self._require_valid_reaction_type(payload.reaction_type_id)
        await self._require_target_allows_user(user_id, payload)
        reaction_was_added = await self._toggle_reaction_row(user_id, payload)
        await self._session.commit()
        summary = await self._load_summary_for_target(user_id, payload)
        return SetUserReactionOutcome(summary=summary, reaction_was_added=reaction_was_added)

    async def _require_valid_reaction_type(self, reaction_type_id: int) -> None:
        row = (
            await self._session.execute(
                select(ReactionType.id).where(ReactionType.id == reaction_type_id)
            )
        ).scalar_one_or_none()
        if row is None:
            raise ReactionTypeInvalidError()

    def _owner_id_select(self, payload: SetUserReactionInput) -> Select[Any]:
        tid = payload.target_id
        kind = payload.target_kind
        if kind == ReactionTargetKind.CARD:
            return select(UserCard.user_id).where(UserCard.id == tid)
        if kind == ReactionTargetKind.CARD_COMMENT:
            return select(CardComment.user_id).where(CardComment.id == tid)
        if kind == ReactionTargetKind.FEED_POST_COMMENT:
            return select(FeedPostComment.user_id).where(FeedPostComment.id == tid)
        if kind == ReactionTargetKind.FEED_POST:
            return select(FeedPost.user_id).where(FeedPost.id == tid)
        raise ReactionTypeInvalidError()

    async def _require_target_allows_user(
        self, user_id: UUID, payload: SetUserReactionInput
    ) -> None:
        owner_id = (
            await self._session.execute(self._owner_id_select(payload))
        ).scalar_one_or_none()
        if owner_id is None:
            raise ReactionTargetNotFoundError()
        if not ALLOW_SELF_REACTION and owner_id == user_id:
            raise SelfReactionForbiddenError()

    async def _toggle_reaction_row(self, user_id: UUID, payload: SetUserReactionInput) -> bool:
        existing = (
            await self._session.execute(
                select(UserReaction).where(
                    UserReaction.user_id == user_id,
                    UserReaction.target_kind == payload.target_kind.value,
                    UserReaction.target_id == payload.target_id,
                    UserReaction.reaction_type_id == payload.reaction_type_id,
                )
            )
        ).scalar_one_or_none()
        reaction_was_added = existing is None
        if existing is not None:
            await self._session.delete(existing)
        else:
            self._session.add(
                UserReaction(
                    user_id=user_id,
                    reaction_type_id=payload.reaction_type_id,
                    target_kind=payload.target_kind.value,
                    target_id=payload.target_id,
                )
            )
        return reaction_was_added

    async def _load_summary_for_target(
        self, user_id: UUID, payload: SetUserReactionInput
    ) -> ReactionTargetSummary:
        cards: list[int] = []
        comments: list[int] = []
        feed_post_comments: list[int] = []
        feed_posts: list[int] = []
        tid = payload.target_id
        if payload.target_kind == ReactionTargetKind.CARD:
            cards = [tid]
        elif payload.target_kind == ReactionTargetKind.CARD_COMMENT:
            comments = [tid]
        elif payload.target_kind == ReactionTargetKind.FEED_POST_COMMENT:
            feed_post_comments = [tid]
        else:
            feed_posts = [tid]

        card_m, comment_m, fpc_m, fp_m = await GetReactionSummariesForTargetsService(
            self._session
        ).execute(
            viewer_user_id=user_id,
            movie_card_ids=cards,
            comment_ids=comments,
            feed_post_comment_ids=feed_post_comments,
            feed_post_ids=feed_posts,
        )
        if cards:
            return card_m[payload.target_id]
        if comments:
            return comment_m[payload.target_id]
        if feed_post_comments:
            return fpc_m[payload.target_id]
        return fp_m[payload.target_id]
