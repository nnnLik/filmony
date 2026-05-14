from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from conf.settings import settings
from models.reaction_target_kind import ReactionTargetKind
from models.reaction_type import ReactionType
from models.user import User
from models.user_reaction import UserReaction
from utils.reaction_urls import resolve_reaction_media_url

from .types import ReactionActorEntry, ReactionCountEntry, ReactionTargetSummary

REACTION_REACTORS_EMBED_CAP = 25


def _scope_conditions_for_ids(
    movie_card_ids: list[int],
    comment_ids: list[int],
    fp_comment_ids: list[int],
    feed_post_ids: list[int],
) -> list:
    scope_conds: list = []
    if movie_card_ids:
        scope_conds.append(
            and_(
                UserReaction.target_kind == ReactionTargetKind.CARD.value,
                UserReaction.target_id.in_(movie_card_ids),
            )
        )
    if comment_ids:
        scope_conds.append(
            and_(
                UserReaction.target_kind == ReactionTargetKind.CARD_COMMENT.value,
                UserReaction.target_id.in_(comment_ids),
            )
        )
    if fp_comment_ids:
        scope_conds.append(
            and_(
                UserReaction.target_kind == ReactionTargetKind.FEED_POST_COMMENT.value,
                UserReaction.target_id.in_(fp_comment_ids),
            )
        )
    if feed_post_ids:
        scope_conds.append(
            and_(
                UserReaction.target_kind == ReactionTargetKind.FEED_POST.value,
                UserReaction.target_id.in_(feed_post_ids),
            )
        )
    return scope_conds


def _actor_tuple_map_from_rows(
    actor_rows: list,
) -> dict[tuple[str, int, int], tuple[ReactionActorEntry, ...]]:
    actors_lists: dict[tuple[str, int, int], list[ReactionActorEntry]] = defaultdict(list)
    for row in actor_rows:
        kind, tid, rtid, uid, slug, dname, uname, fn, ln, photo = row
        key = (str(kind), int(tid), int(rtid))
        actors_lists[key].append(
            ReactionActorEntry(
                id=uid,
                profile_slug=str(slug),
                display_name=dname,
                username=uname,
                first_name=fn,
                last_name=ln,
                photo_url=photo,
            )
        )
    return {k: tuple(v) for k, v in actors_lists.items()}


def _set_summary_counts_if_member(
    kind: str,
    tid: int,
    ordered: tuple[ReactionCountEntry, ...],
    card_out: dict[int, ReactionTargetSummary],
    comment_out: dict[int, ReactionTargetSummary],
    feed_post_comment_out: dict[int, ReactionTargetSummary],
    feed_post_out: dict[int, ReactionTargetSummary],
) -> None:
    if kind == ReactionTargetKind.CARD.value and tid in card_out:
        prev = card_out[tid]
        card_out[tid] = ReactionTargetSummary(
            counts=ordered, my_reaction_type_ids=prev.my_reaction_type_ids
        )
    elif kind == ReactionTargetKind.CARD_COMMENT.value and tid in comment_out:
        prev = comment_out[tid]
        comment_out[tid] = ReactionTargetSummary(
            counts=ordered, my_reaction_type_ids=prev.my_reaction_type_ids
        )
    elif kind == ReactionTargetKind.FEED_POST_COMMENT.value and tid in feed_post_comment_out:
        prev = feed_post_comment_out[tid]
        feed_post_comment_out[tid] = ReactionTargetSummary(
            counts=ordered, my_reaction_type_ids=prev.my_reaction_type_ids
        )
    elif kind == ReactionTargetKind.FEED_POST.value and tid in feed_post_out:
        prev = feed_post_out[tid]
        feed_post_out[tid] = ReactionTargetSummary(
            counts=ordered, my_reaction_type_ids=prev.my_reaction_type_ids
        )


def _set_summary_mine_if_member(
    kind: str,
    tid: int,
    unique_ids: tuple[int, ...],
    card_out: dict[int, ReactionTargetSummary],
    comment_out: dict[int, ReactionTargetSummary],
    feed_post_comment_out: dict[int, ReactionTargetSummary],
    feed_post_out: dict[int, ReactionTargetSummary],
) -> None:
    if kind == ReactionTargetKind.CARD.value and tid in card_out:
        s = card_out[tid]
        card_out[tid] = ReactionTargetSummary(counts=s.counts, my_reaction_type_ids=unique_ids)
    elif kind == ReactionTargetKind.CARD_COMMENT.value and tid in comment_out:
        s = comment_out[tid]
        comment_out[tid] = ReactionTargetSummary(counts=s.counts, my_reaction_type_ids=unique_ids)
    elif kind == ReactionTargetKind.FEED_POST_COMMENT.value and tid in feed_post_comment_out:
        s = feed_post_comment_out[tid]
        feed_post_comment_out[tid] = ReactionTargetSummary(
            counts=s.counts, my_reaction_type_ids=unique_ids
        )
    elif kind == ReactionTargetKind.FEED_POST.value and tid in feed_post_out:
        s = feed_post_out[tid]
        feed_post_out[tid] = ReactionTargetSummary(counts=s.counts, my_reaction_type_ids=unique_ids)


class GetReactionSummariesForTargetsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        *,
        viewer_user_id: UUID,
        movie_card_ids: list[int],
        comment_ids: list[int],
        feed_post_comment_ids: list[int] | None = None,
        feed_post_ids: list[int] | None = None,
    ) -> tuple[
        dict[int, ReactionTargetSummary],
        dict[int, ReactionTargetSummary],
        dict[int, ReactionTargetSummary],
        dict[int, ReactionTargetSummary],
    ]:
        fp_comment_ids = feed_post_comment_ids if feed_post_comment_ids is not None else []
        fpost_ids = feed_post_ids if feed_post_ids is not None else []
        card_out: dict[int, ReactionTargetSummary] = {
            cid: ReactionTargetSummary(counts=(), my_reaction_type_ids=()) for cid in movie_card_ids
        }
        comment_out: dict[int, ReactionTargetSummary] = {
            cid: ReactionTargetSummary(counts=(), my_reaction_type_ids=()) for cid in comment_ids
        }
        feed_post_comment_out: dict[int, ReactionTargetSummary] = {
            cid: ReactionTargetSummary(counts=(), my_reaction_type_ids=()) for cid in fp_comment_ids
        }
        feed_post_out: dict[int, ReactionTargetSummary] = {
            pid: ReactionTargetSummary(counts=(), my_reaction_type_ids=()) for pid in fpost_ids
        }

        scope_conds = _scope_conditions_for_ids(
            movie_card_ids, comment_ids, fp_comment_ids, fpost_ids
        )
        if not scope_conds:
            return card_out, comment_out, feed_post_comment_out, feed_post_out

        scope = or_(*scope_conds)

        rx = UserReaction
        ranked = (
            select(
                rx.target_kind,
                rx.target_id,
                rx.reaction_type_id,
                rx.user_id,
                func.row_number()
                .over(
                    partition_by=(rx.target_kind, rx.target_id, rx.reaction_type_id),
                    order_by=rx.id.desc(),
                )
                .label('rn'),
            ).where(scope)
        ).subquery()

        actors_stmt = (
            select(
                ranked.c.target_kind,
                ranked.c.target_id,
                ranked.c.reaction_type_id,
                User.id,
                User.profile_slug,
                User.display_name,
                User.username,
                User.first_name,
                User.last_name,
                User.photo_url,
            )
            .join(User, User.id == ranked.c.user_id)
            .where(ranked.c.rn <= REACTION_REACTORS_EMBED_CAP)
            .order_by(
                ranked.c.target_kind,
                ranked.c.target_id,
                ranked.c.reaction_type_id,
                ranked.c.rn,
            )
        )
        actor_rows = (await self._session.execute(actors_stmt)).all()
        actors_tuple_map = _actor_tuple_map_from_rows(actor_rows)

        media_base = settings.reaction_media.public_base_url

        count_stmt = (
            select(
                UserReaction.target_kind,
                UserReaction.target_id,
                UserReaction.reaction_type_id,
                func.count(UserReaction.id).label('cnt'),
                func.bool_or(UserReaction.user_id == viewer_user_id).label('viewer_has'),
                ReactionType.asset_key,
                ReactionType.image_url,
            )
            .join(ReactionType, ReactionType.id == UserReaction.reaction_type_id)
            .where(scope)
            .group_by(
                UserReaction.target_kind,
                UserReaction.target_id,
                UserReaction.reaction_type_id,
                ReactionType.asset_key,
                ReactionType.image_url,
            )
        )
        count_rows = (await self._session.execute(count_stmt)).all()

        buckets: dict[tuple[str, int], list[ReactionCountEntry]] = defaultdict(list)
        mines_acc: defaultdict[tuple[str, int], list[int]] = defaultdict(list)
        for row in count_rows:
            kind, tid, rtid, cnt, viewer_has, asset_key, url = row
            resolved_url = resolve_reaction_media_url(
                asset_key=asset_key,
                image_url_fallback=str(url),
                public_base=media_base,
            )
            rkey = (str(kind), int(tid), int(rtid))
            buckets[(kind, tid)].append(
                ReactionCountEntry(
                    reaction_type_id=int(rtid),
                    count=int(cnt),
                    image_url=resolved_url,
                    asset_key=str(asset_key),
                    reactors=actors_tuple_map.get(rkey, ()),
                )
            )
            if viewer_has:
                mines_acc[(str(kind), int(tid))].append(int(rtid))

        for key, entries in buckets.items():
            kind, tid = key
            ordered = tuple(sorted(entries, key=lambda e: (e.asset_key, e.reaction_type_id)))
            _set_summary_counts_if_member(
                kind, tid, ordered, card_out, comment_out, feed_post_comment_out, feed_post_out
            )

        for (kind, tid), rtids in mines_acc.items():
            unique_ids = tuple(dict.fromkeys(rtids))
            _set_summary_mine_if_member(
                kind, tid, unique_ids, card_out, comment_out, feed_post_comment_out, feed_post_out
            )

        return card_out, comment_out, feed_post_comment_out, feed_post_out
