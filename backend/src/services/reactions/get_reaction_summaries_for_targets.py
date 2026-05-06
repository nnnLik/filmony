from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from conf.settings import settings
from models.reaction_target_kind import ReactionTargetKind
from models.reaction_type import ReactionType
from models.user_reaction import UserReaction
from utils.reaction_urls import resolve_reaction_media_url

from .types import ReactionCountEntry, ReactionTargetSummary


class GetReactionSummariesForTargetsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        *,
        viewer_user_id: UUID,
        movie_card_ids: list[int],
        comment_ids: list[int],
    ) -> tuple[dict[int, ReactionTargetSummary], dict[int, ReactionTargetSummary]]:
        card_out: dict[int, ReactionTargetSummary] = {
            cid: ReactionTargetSummary(counts=(), my_reaction_type_ids=()) for cid in movie_card_ids
        }
        comment_out: dict[int, ReactionTargetSummary] = {
            cid: ReactionTargetSummary(counts=(), my_reaction_type_ids=()) for cid in comment_ids
        }

        scope_conds: list = []
        if movie_card_ids:
            scope_conds.append(
                and_(
                    UserReaction.target_kind == ReactionTargetKind.MOVIE_CARD.value,
                    UserReaction.target_id.in_(movie_card_ids),
                )
            )
        if comment_ids:
            scope_conds.append(
                and_(
                    UserReaction.target_kind == ReactionTargetKind.MOVIE_CARD_COMMENT.value,
                    UserReaction.target_id.in_(comment_ids),
                )
            )
        if not scope_conds:
            return card_out, comment_out

        scope = or_(*scope_conds)

        media_base = settings.reaction_media.public_base_url

        count_stmt = (
            select(
                UserReaction.target_kind,
                UserReaction.target_id,
                UserReaction.reaction_type_id,
                func.count(UserReaction.id).label('cnt'),
                ReactionType.asset_key,
                ReactionType.image_url,
                ReactionType.label,
                ReactionType.sort_order,
            )
            .join(ReactionType, ReactionType.id == UserReaction.reaction_type_id)
            .where(scope)
            .group_by(
                UserReaction.target_kind,
                UserReaction.target_id,
                UserReaction.reaction_type_id,
                ReactionType.asset_key,
                ReactionType.image_url,
                ReactionType.label,
                ReactionType.sort_order,
            )
        )
        count_rows = (await self._session.execute(count_stmt)).all()

        buckets: dict[tuple[str, int], list[ReactionCountEntry]] = defaultdict(list)
        for row in count_rows:
            kind, tid, rtid, cnt, asset_key, url, lab, so = row
            resolved_url = resolve_reaction_media_url(
                asset_key=asset_key,
                image_url_fallback=str(url),
                public_base=media_base,
            )
            buckets[(kind, tid)].append(
                ReactionCountEntry(
                    reaction_type_id=int(rtid),
                    count=int(cnt),
                    image_url=resolved_url,
                    label=lab,
                    sort_order=int(so),
                )
            )

        for key, entries in buckets.items():
            kind, tid = key
            ordered = tuple(sorted(entries, key=lambda e: (e.sort_order, e.reaction_type_id)))
            if kind == ReactionTargetKind.MOVIE_CARD.value and tid in card_out:
                prev = card_out[tid]
                card_out[tid] = ReactionTargetSummary(
                    counts=ordered, my_reaction_type_ids=prev.my_reaction_type_ids
                )
            elif kind == ReactionTargetKind.MOVIE_CARD_COMMENT.value and tid in comment_out:
                prev = comment_out[tid]
                comment_out[tid] = ReactionTargetSummary(
                    counts=ordered, my_reaction_type_ids=prev.my_reaction_type_ids
                )

        mines: defaultdict[tuple[str, int], list[int]] = defaultdict(list)
        mine_stmt = select(
            UserReaction.target_kind, UserReaction.target_id, UserReaction.reaction_type_id
        ).where(UserReaction.user_id == viewer_user_id, scope)
        mine_rows = (await self._session.execute(mine_stmt)).all()
        for kind, tid, rtid in mine_rows:
            mines[(kind, int(tid))].append(int(rtid))

        for (kind, tid), rtids in mines.items():
            unique_ids = tuple(dict.fromkeys(rtids))
            if kind == ReactionTargetKind.MOVIE_CARD.value and tid in card_out:
                s = card_out[tid]
                card_out[tid] = ReactionTargetSummary(
                    counts=s.counts, my_reaction_type_ids=unique_ids
                )
            elif kind == ReactionTargetKind.MOVIE_CARD_COMMENT.value and tid in comment_out:
                s = comment_out[tid]
                comment_out[tid] = ReactionTargetSummary(
                    counts=s.counts, my_reaction_type_ids=unique_ids
                )

        return card_out, comment_out
