"""Политика self-react: см. `.cursor/features/movie-card-custom-reactions/feature.md` (разрешено по умолчанию)."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.movie_card import MovieCard
from models.movie_card_comment import MovieCardComment
from models.reaction_target_kind import ReactionTargetKind
from models.reaction_type import ReactionType
from models.user_reaction import UserReaction

from .get_reaction_summaries_for_targets import GetReactionSummariesForTargetsService
from .touch_user_recent_reaction import TouchUserRecentReactionService
from .types import ReactionTargetSummary

ALLOW_SELF_REACTION = True


@dataclass(frozen=True, slots=True)
class SetUserReactionInput:
    target_kind: ReactionTargetKind
    target_id: int
    reaction_type_id: int


class ReactionTypeInvalidError(Exception):
    pass


class ReactionTargetNotFoundError(Exception):
    pass


class SelfReactionForbiddenError(Exception):
    pass


class SetOrToggleUserReactionService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, user_id: UUID, payload: SetUserReactionInput) -> ReactionTargetSummary:
        reaction_type_row = (
            await self._session.execute(
                select(ReactionType.id, ReactionType.is_active).where(
                    ReactionType.id == payload.reaction_type_id
                )
            )
        ).one_or_none()
        if reaction_type_row is None or not reaction_type_row[1]:
            raise ReactionTypeInvalidError()

        if payload.target_kind == ReactionTargetKind.MOVIE_CARD:
            owner_id = (
                await self._session.execute(
                    select(MovieCard.user_id).where(MovieCard.id == payload.target_id)
                )
            ).scalar_one_or_none()
            if owner_id is None:
                raise ReactionTargetNotFoundError()
            if not ALLOW_SELF_REACTION and owner_id == user_id:
                raise SelfReactionForbiddenError()
        elif payload.target_kind == ReactionTargetKind.MOVIE_CARD_COMMENT:
            owner_id = (
                await self._session.execute(
                    select(MovieCardComment.user_id).where(MovieCardComment.id == payload.target_id)
                )
            ).scalar_one_or_none()
            if owner_id is None:
                raise ReactionTargetNotFoundError()
            if not ALLOW_SELF_REACTION and owner_id == user_id:
                raise SelfReactionForbiddenError()
        else:
            raise ReactionTypeInvalidError()

        existing = (
            await self._session.execute(
                select(UserReaction).where(
                    UserReaction.user_id == user_id,
                    UserReaction.target_kind == payload.target_kind.value,
                    UserReaction.target_id == payload.target_id,
                )
            )
        ).scalar_one_or_none()

        if existing is None:
            self._session.add(
                UserReaction(
                    user_id=user_id,
                    reaction_type_id=payload.reaction_type_id,
                    target_kind=payload.target_kind.value,
                    target_id=payload.target_id,
                )
            )
        elif existing.reaction_type_id == payload.reaction_type_id:
            await self._session.delete(existing)
        else:
            existing.reaction_type_id = payload.reaction_type_id

        await self._session.commit()

        # Точка расширения для Telegram / outbox (уведомления о реакциях вне scope MVP).
        cards: list[int] = []
        comments: list[int] = []
        if payload.target_kind == ReactionTargetKind.MOVIE_CARD:
            cards = [payload.target_id]
        else:
            comments = [payload.target_id]

        card_m, comment_m = await GetReactionSummariesForTargetsService(self._session).execute(
            viewer_user_id=user_id,
            movie_card_ids=cards,
            comment_ids=comments,
        )
        summary = card_m[payload.target_id] if cards else comment_m[payload.target_id]

        if summary.my_reaction_type_id is not None:
            await TouchUserRecentReactionService(self._session).execute(
                user_id=user_id,
                reaction_type_id=summary.my_reaction_type_id,
            )
            await self._session.commit()

        return summary
