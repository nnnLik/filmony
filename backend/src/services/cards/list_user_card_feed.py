from __future__ import annotations

import asyncio
import base64
import binascii
import datetime as dt
from dataclasses import dataclass, field, replace
from typing import Any, Literal
from uuid import UUID

import orjson
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

import const.feed
from const.feed import FeedMode
from models.card_comment import CardComment
from models.card_tag import CardTag
from models.catalog_item import CatalogItem, CatalogProvider
from models.feed_post import FeedPost
from models.feed_post_comment import FeedPostComment
from models.film import Film
from models.game import Game
from models.user import User
from models.user_card import UserCard
from models.user_card_category import DEFAULT_USER_CARD_CATEGORY_NAME, UserCardCategory
from models.user_subscription import UserSubscription
from services.cards.batch_resolve_comment_inline_refs import batch_resolve_comment_inline_refs
from services.cards.card_catalog_release_fields import universal_release_year_date
from services.cards.inline_user_card_ref_tokens import ReferencedInlineUserCardSnippet
from services.cards.list_user_card_comments import UserCardCommentAuthor, UserCardCommentItem
from services.feed_posts.list_feed_post_comments import FeedPostCommentItem
from services.profile.batch_resolve_inline_mentions import ReferencedMentionSnippet
from services.reactions import GetReactionSummariesForTargetsService
from services.reactions.types import ReactionTargetSummary

CURSOR_PREFIX = 'v1.'


def _empty_reaction_summary() -> ReactionTargetSummary:
    return ReactionTargetSummary(counts=(), my_reaction_type_ids=())


@dataclass(frozen=True, slots=True)
class FeedPostEngagementSnapshot:
    """Результат `_load_feed_post_engagement_maps` для повторного использования в `attach_*`."""

    counts_by_post: dict[int, int]
    previews_by_post: dict[int, list[FeedPostCommentItem]]
    fp_reactions: dict[int, ReactionTargetSummary]


async def _load_feed_post_engagement_maps(
    session: AsyncSession,
    viewer_user_id: UUID,
    post_ids: list[int],
) -> tuple[dict[int, int], dict[int, list[FeedPostCommentItem]], dict[int, ReactionTargetSummary]]:
    """Счётчики комментариев, превью корневых комментариев (до 3 на пост) и реакции на посты/превью."""
    if not post_ids:
        return {}, {}, {}

    counts_by_post: dict[int, int] = dict.fromkeys(post_ids, 0)
    count_rows = (
        await session.execute(
            select(FeedPostComment.feed_post_id, func.count(FeedPostComment.id))
            .where(FeedPostComment.feed_post_id.in_(post_ids))
            .group_by(FeedPostComment.feed_post_id)
        )
    ).all()
    for fpid, cnt in count_rows:
        counts_by_post[int(fpid)] = int(cnt)

    ranked = (
        select(
            FeedPostComment.id,
            FeedPostComment.feed_post_id,
            FeedPostComment.user_id,
            FeedPostComment.parent_comment_id,
            FeedPostComment.text,
            FeedPostComment.created_at,
            func.row_number()
            .over(
                partition_by=FeedPostComment.feed_post_id,
                order_by=FeedPostComment.id.desc(),
            )
            .label('rn'),
        )
        .where(
            FeedPostComment.feed_post_id.in_(post_ids),
            FeedPostComment.parent_comment_id.is_(None),
        )
        .subquery()
    )

    preview_stmt = (
        select(
            ranked.c.id,
            ranked.c.feed_post_id,
            ranked.c.parent_comment_id,
            ranked.c.text,
            ranked.c.created_at,
            User,
        )
        .join(User, User.id == ranked.c.user_id)
        .where(ranked.c.rn <= 3)
        .order_by(ranked.c.feed_post_id.asc(), ranked.c.id.asc())
    )
    preview_rows = (await session.execute(preview_stmt)).all()

    previews_by_post: dict[int, list[FeedPostCommentItem]] = {pid: [] for pid in post_ids}
    preview_comment_ids: list[int] = []
    for cid, fpid, parent_comment_id, text, created_at, author_row in preview_rows:
        preview_comment_ids.append(int(cid))
        previews_by_post[int(fpid)].append(
            FeedPostCommentItem(
                id=int(cid),
                feed_post_id=int(fpid),
                parent_comment_id=parent_comment_id,
                text=text,
                created_at=created_at,
                replies_count=0,
                total_descendants_count=0,
                author=UserCardCommentAuthor(
                    id=author_row.id,
                    profile_slug=author_row.profile_slug,
                    username=author_row.username,
                    first_name=author_row.first_name,
                    last_name=author_row.last_name,
                    photo_url=author_row.photo_url,
                    display_name=author_row.display_name,
                ),
                reactions=_empty_reaction_summary(),
            )
        )

    _, _, fpc_rx, fp_rx = await GetReactionSummariesForTargetsService(session).execute(
        viewer_user_id=viewer_user_id,
        user_card_ids=[],
        comment_ids=[],
        feed_post_comment_ids=preview_comment_ids,
        feed_post_ids=post_ids,
    )

    for pid, plist in list(previews_by_post.items()):
        previews_by_post[pid] = [replace(p, reactions=fpc_rx[p.id]) for p in plist]

    return counts_by_post, previews_by_post, fp_rx


async def enrich_feed_post_items_for_feed_paths(
    session: AsyncSession,
    items: list[FeedPostFeedItem],
) -> list[FeedPostFeedItem]:
    """⟦c⟧ и ⟦@⟧ для тел постов и превью комментариев без повторной загрузки счётчиков."""
    if not items:
        return []
    body_pairs = [(it.user_id, it.body) for it in items]
    body_snips_list, body_men_list = await batch_resolve_comment_inline_refs(session, body_pairs)

    preview_pairs: list[tuple[UUID, str]] = []
    for it in items:
        for c in it.comments_preview:
            preview_pairs.append((c.author.id, c.text))
    if preview_pairs:
        preview_snips_list, preview_men_list = await batch_resolve_comment_inline_refs(
            session, preview_pairs
        )
    else:
        preview_snips_list = []
        preview_men_list = []

    snip_i = 0
    out: list[FeedPostFeedItem] = []
    for idx, it in enumerate(items):
        upgraded: list[FeedPostCommentItem] = []
        for c in it.comments_preview:
            snips = preview_snips_list[snip_i]
            mens = preview_men_list[snip_i]
            snip_i += 1
            upgraded.append(
                replace(c, referenced_inline_user_cards=snips, referenced_mentions=mens),
            )
        out.append(
            replace(
                it,
                comments_preview=tuple(upgraded),
                body_referenced_inline_user_cards=body_snips_list[idx],
                body_referenced_mentions=body_men_list[idx],
            ),
        )
    return out


async def enrich_feed_posts_source_comments(
    session: AsyncSession,
    items: list[FeedPostFeedItem],
) -> list[FeedPostFeedItem]:
    """Подмешивает текст и автора исходного комментария для постов с ``source_comment_id``."""
    if not items:
        return []
    wanted = {it.source_comment_id for it in items if it.source_comment_id is not None}
    if not wanted:
        return items
    stmt = (
        select(CardComment, User)
        .join(User, User.id == CardComment.user_id)
        .where(CardComment.id.in_(wanted))
    )
    rows = (await session.execute(stmt)).all()
    by_comment_id: dict[int, tuple[CardComment, User]] = {int(c.id): (c, u) for c, u in rows}

    pairs: list[tuple[UUID, str]] = []
    pair_meta: list[tuple[int, CardComment, User]] = []
    for sid in sorted(wanted):
        row = by_comment_id.get(sid)
        if row is None:
            continue
        comm, usr = row
        pairs.append((comm.user_id, comm.text or ''))
        pair_meta.append((sid, comm, usr))

    if not pairs:
        return items

    snips_list, mens_list = await batch_resolve_comment_inline_refs(session, pairs)

    snippet_by_comment_id: dict[int, FeedPostSourceCommentSnippet] = {}
    for i, (sid, comm, usr) in enumerate(pair_meta):
        author = UserCardCommentAuthor(
            id=usr.id,
            profile_slug=usr.profile_slug,
            username=usr.username,
            first_name=usr.first_name,
            last_name=usr.last_name,
            photo_url=usr.photo_url,
            display_name=usr.display_name,
        )
        snippet_by_comment_id[sid] = FeedPostSourceCommentSnippet(
            id=int(comm.id),
            text=comm.text or '',
            image_url=comm.image_url,
            author=author,
            referenced_inline_user_cards=snips_list[i],
            referenced_mentions=mens_list[i],
        )

    return [
        replace(
            it,
            source_comment=(
                snippet_by_comment_id[it.source_comment_id]
                if it.source_comment_id is not None
                and it.source_comment_id in snippet_by_comment_id
                else None
            ),
        )
        for it in items
    ]


async def attach_feed_post_list_engagement(
    session: AsyncSession,
    viewer_user_id: UUID,
    items: list[FeedPostFeedItem],
    *,
    engagement: FeedPostEngagementSnapshot | None = None,
) -> list[FeedPostFeedItem]:
    """Дополняет посты счётчиком/превью комментариев и реакциями (профиль, детальная страница)."""
    if not items:
        return []
    post_ids = [it.id for it in items]
    if engagement is None:
        counts_by_post, previews_by_post, fp_rx = await _load_feed_post_engagement_maps(
            session, viewer_user_id, post_ids
        )
    else:
        counts_by_post = engagement.counts_by_post
        previews_by_post = engagement.previews_by_post
        fp_rx = engagement.fp_reactions

    body_pairs = [(it.user_id, it.body) for it in items]
    body_snips_list, body_men_list = await batch_resolve_comment_inline_refs(session, body_pairs)

    preview_pairs: list[tuple[UUID, str]] = []
    for it in items:
        for c in previews_by_post.get(it.id, []):
            preview_pairs.append((c.author.id, c.text))
    if preview_pairs:
        preview_snips_list, preview_men_list = await batch_resolve_comment_inline_refs(
            session, preview_pairs
        )
    else:
        preview_snips_list = []
        preview_men_list = []

    snip_i = 0
    upgraded_by_post: dict[int, tuple[FeedPostCommentItem, ...]] = {}
    for it in items:
        pid = it.id
        raw_prev = previews_by_post.get(pid, [])
        upgraded: list[FeedPostCommentItem] = []
        for c in raw_prev:
            snips = preview_snips_list[snip_i]
            mens = preview_men_list[snip_i]
            snip_i += 1
            upgraded.append(
                replace(c, referenced_inline_user_cards=snips, referenced_mentions=mens)
            )
        upgraded_by_post[pid] = tuple(upgraded)

    merged = [
        replace(
            it,
            reactions=fp_rx[it.id],
            comments_count=counts_by_post.get(it.id, 0),
            comments_preview=upgraded_by_post.get(it.id, ()),
            body_referenced_inline_user_cards=body_snips_list[idx],
            body_referenced_mentions=body_men_list[idx],
        )
        for idx, it in enumerate(items)
    ]
    return await enrich_feed_posts_source_comments(session, merged)


def _norm_genre(g: str) -> str:
    return g.strip().lower()


def _norm_tag(t: str) -> str:
    return t.strip().lower()


def _parse_cursor_offsets(off: Any) -> dict[str, int] | None:
    if not isinstance(off, dict):
        return None
    offsets = dict.fromkeys(const.feed.STREAM_KEYS, 0)
    for k in const.feed.STREAM_KEYS:
        if k not in off:
            continue
        try:
            offsets[k] = int(off[k])
        except (TypeError, ValueError):
            return None
    return offsets


@dataclass(frozen=True, slots=True)
class UserCardFeedItem:
    id: int
    user_id: UUID
    card_author: UserCardCommentAuthor
    provider: CatalogProvider
    external_id: str | None
    film_id: int | None
    film_kinopoisk_id: int | None
    film_genres: list[str]
    film_title: str
    film_year: int | None
    release_year: int | None
    release_date: str | None
    film_poster_url: str | None
    catalog_item_id: int | None
    display_title: str
    display_cover_url: str | None
    display_summary: str | None
    rating: float
    company: str
    mood_before: str
    mood_after: str
    watch_note: str
    custom_tags: list[str]
    comments_count: int
    comments_preview: list[UserCardCommentItem]
    reactions: ReactionTargetSummary
    feed_source: const.feed.StreamName
    is_favorite: bool
    is_planned: bool
    category_id: int
    category_name: str
    audio_url: str | None


@dataclass(frozen=True, slots=True)
class FeedPostReferencedCardSnippet:
    user_card_id: int
    film_title: str
    film_year: int | None
    release_year: int | None
    release_date: str | None
    film_poster_url: str | None
    rating: float
    is_planned: bool = False


@dataclass(frozen=True, slots=True)
class FeedPostSourceCommentSnippet:
    """Исходный комментарий к карточке, из которого сделан пост (для цитаты в UI)."""

    id: int
    text: str
    image_url: str | None
    author: UserCardCommentAuthor
    referenced_inline_user_cards: tuple[ReferencedInlineUserCardSnippet, ...] = ()
    referenced_mentions: tuple[ReferencedMentionSnippet, ...] = ()


@dataclass(frozen=True, slots=True)
class FeedPostFeedItem:
    id: int
    user_id: UUID
    author: UserCardCommentAuthor
    body: str
    image_url: str | None
    referenced_user_card_id: int | None
    source_comment_id: int | None
    created_at: dt.datetime
    feed_source: const.feed.StreamName
    referenced_card: FeedPostReferencedCardSnippet | None
    reactions: ReactionTargetSummary = field(default_factory=_empty_reaction_summary)
    comments_count: int = 0
    comments_preview: tuple[FeedPostCommentItem, ...] = ()
    body_referenced_inline_user_cards: tuple[ReferencedInlineUserCardSnippet, ...] = ()
    body_referenced_mentions: tuple[ReferencedMentionSnippet, ...] = ()
    source_comment: FeedPostSourceCommentSnippet | None = None


FeedPageEntry = UserCardFeedItem | FeedPostFeedItem


@dataclass(frozen=True, slots=True)
class UserCardFeedPage:
    items: list[FeedPageEntry]
    next_cursor: str | None


@dataclass
class _MergeState:
    offsets: dict[str, int]
    slot_index: int
    seen_cards: set[int]
    seen_posts: set[int]
    tail_author_ids: list[str]
    tail_linked_film_ids: list[int]
    feed_mode: FeedMode

    @classmethod
    def initial(cls, feed_mode: FeedMode = 'default') -> _MergeState:
        return cls(
            offsets=dict.fromkeys(const.feed.STREAM_KEYS, 0),
            slot_index=0,
            seen_cards=set(),
            seen_posts=set(),
            tail_author_ids=[],
            tail_linked_film_ids=[],
            feed_mode=feed_mode,
        )

    @classmethod
    def from_cursor_payload(cls, data: dict[str, Any]) -> _MergeState | None:
        if data.get('v') != 1:
            return None
        offsets = _parse_cursor_offsets(data.get('offsets'))
        if offsets is None:
            return None
        seen_cards: set[int] = set()
        seen_posts: set[int] = set()
        sc = data.get('seen_cards')
        if isinstance(sc, list):
            seen_cards = {int(x) for x in sc}
        else:
            legacy = data.get('seen', [])
            if isinstance(legacy, list):
                seen_cards = {int(x) for x in legacy}
            else:
                return None
        sp = data.get('seen_posts', [])
        if isinstance(sp, list):
            seen_posts = {int(x) for x in sp}
        ta = data.get('tail_authors', [])
        tf = data.get('tail_films', [])
        if not isinstance(ta, list) or not isinstance(tf, list):
            return None
        raw_mode = data.get('mode', 'default')
        if raw_mode not in const.feed.VALID_FEED_MODES:
            return None
        return cls(
            offsets=offsets,
            slot_index=int(data.get('slot_index', 0)),
            seen_cards=seen_cards,
            seen_posts=seen_posts,
            tail_author_ids=[str(x) for x in ta],
            tail_linked_film_ids=[int(x) for x in tf],
            feed_mode=raw_mode,
        )

    def to_payload(self) -> dict[str, Any]:
        cap = const.feed.FEED_CURSOR_SEEN_MAX
        sc_list = sorted(self.seen_cards)
        if len(sc_list) > cap:
            sc_list = sc_list[-cap:]
        sp_list = sorted(self.seen_posts)
        if len(sp_list) > cap:
            sp_list = sp_list[-cap:]
        return {
            'v': 1,
            'offsets': {k: self.offsets[k] for k in const.feed.STREAM_KEYS},
            'slot_index': self.slot_index,
            'seen_cards': sc_list,
            'seen_posts': sp_list,
            'tail_authors': list(self.tail_author_ids),
            'tail_films': list(self.tail_linked_film_ids),
            'mode': self.feed_mode,
        }

    def clone(self) -> _MergeState:
        return _MergeState(
            offsets=dict(self.offsets),
            slot_index=self.slot_index,
            seen_cards=set(self.seen_cards),
            seen_posts=set(self.seen_posts),
            tail_author_ids=list(self.tail_author_ids),
            tail_linked_film_ids=list(self.tail_linked_film_ids),
            feed_mode=self.feed_mode,
        )


def _encode_cursor(state: _MergeState) -> str:
    raw = orjson.dumps(state.to_payload())
    b64 = base64.urlsafe_b64encode(raw).decode('ascii').rstrip('=')
    return f'{CURSOR_PREFIX}{b64}'


def _decode_cursor(cursor: str | None) -> _MergeState | None:
    if cursor is None or cursor == '':
        return None
    if not cursor.startswith(CURSOR_PREFIX):
        return None
    payload = cursor[len(CURSOR_PREFIX) :]
    pad = (-len(payload)) % 4
    if pad:
        payload += '=' * pad
    try:
        raw = base64.urlsafe_b64decode(payload.encode('ascii'))
        data = orjson.loads(raw)
    except (ValueError, binascii.Error, orjson.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return _MergeState.from_cursor_payload(data)


class ListUserCardFeedService:
    """Собирает персональную ленту: карточки фильмов и текстовые посты из нескольких потоков."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        viewer_user_id: UUID,
        cursor: str | None,
        limit: int,
        *,
        feed_mode: FeedMode = 'default',
    ) -> UserCardFeedPage:
        decoded = _decode_cursor(cursor)
        if decoded is not None and decoded.feed_mode != feed_mode:
            merge_state = _MergeState.initial(feed_mode)
        elif decoded is not None:
            merge_state = decoded
        else:
            merge_state = _MergeState.initial(feed_mode)

        following_ids, follower_ids = await self._load_subscription_sets(viewer_user_id)
        graph_user_ids = {viewer_user_id, *following_ids, *follower_ids}
        genre_profile, tag_profile = await self._load_viewer_affinity_sets(viewer_user_id)

        streams = await self._build_streams(
            viewer_user_id=viewer_user_id,
            following_ids=following_ids,
            follower_ids=follower_ids,
            graph_user_ids=graph_user_ids,
            genre_profile=genre_profile,
            tag_profile=tag_profile,
            feed_mode=feed_mode,
        )
        streams = self._streams_for_mode(streams, feed_mode)

        ordered_picks, next_state, has_more = self._merge_feed(
            merge_state, streams, limit, viewer_user_id
        )

        card_ids_order: list[int] = []
        post_ids_order: list[int] = []
        source_by_card: dict[int, const.feed.StreamName] = {}
        source_by_post: dict[int, const.feed.StreamName] = {}
        for kind, item_id, src in ordered_picks:
            if kind == 'card':
                card_ids_order.append(item_id)
                source_by_card[item_id] = src
            else:
                post_ids_order.append(item_id)
                source_by_post[item_id] = src

        async def _cards_branch() -> list[UserCardFeedItem]:
            visible_rows = await self._load_card_rows_ordered(card_ids_order)
            return await self._hydrate_feed_items(viewer_user_id, visible_rows, source_by_card)

        async def _posts_branch() -> list[FeedPostFeedItem]:
            raw = await self._hydrate_feed_post_items(
                viewer_user_id, post_ids_order, source_by_post
            )
            return await enrich_feed_post_items_for_feed_paths(self._session, raw)

        card_items, post_items = await asyncio.gather(
            _cards_branch(),
            _posts_branch(),
        )
        card_by_id = {it.id: it for it in card_items}
        post_by_id = {it.id: it for it in post_items}

        items: list[FeedPageEntry] = []
        for kind, item_id, _src in ordered_picks:
            if kind == 'card':
                if item_id in card_by_id:
                    items.append(card_by_id[item_id])
            elif item_id in post_by_id:
                items.append(post_by_id[item_id])

        next_cursor: str | None = _encode_cursor(next_state) if has_more else None
        return UserCardFeedPage(items=items, next_cursor=next_cursor)

    def _streams_for_mode(
        self,
        streams: dict[const.feed.StreamName, list[tuple[int, UUID, int]]],
        feed_mode: FeedMode,
    ) -> dict[const.feed.StreamName, list[tuple[int, UUID, int]]]:
        allowed = const.feed.ALLOWED_STREAMS_BY_MODE[feed_mode]
        return {k: (list(v) if k in allowed else []) for k, v in streams.items()}

    async def _load_subscription_sets(self, viewer_id: UUID) -> tuple[set[UUID], set[UUID]]:
        fol = (
            (
                await self._session.execute(
                    select(UserSubscription.following_user_id).where(
                        UserSubscription.follower_user_id == viewer_id
                    )
                )
            )
            .scalars()
            .all()
        )
        sub = (
            (
                await self._session.execute(
                    select(UserSubscription.follower_user_id).where(
                        UserSubscription.following_user_id == viewer_id
                    )
                )
            )
            .scalars()
            .all()
        )
        return set(fol), set(sub)

    async def _load_viewer_affinity_sets(self, viewer_id: UUID) -> tuple[set[str], set[str]]:
        genres_rows = (
            await self._session.execute(
                select(Film.genres)
                .join(UserCard, UserCard.film_id == Film.id)
                .where(UserCard.user_id == viewer_id)
            )
        ).all()
        gset: set[str] = set()
        for (glist,) in genres_rows:
            for g in glist or []:
                gset.add(_norm_genre(str(g)))

        tag_rows = (
            (
                await self._session.execute(
                    select(CardTag.tag)
                    .join(UserCard, UserCard.id == CardTag.card_id)
                    .where(UserCard.user_id == viewer_id)
                )
            )
            .scalars()
            .all()
        )
        tset = {_norm_tag(t) for t in tag_rows}
        return gset, tset

    async def _build_post_stream(
        self,
        *,
        viewer_user_id: UUID,
        following_ids: set[UUID],
        follower_ids: set[UUID],
        feed_mode: FeedMode,
    ) -> list[tuple[int, UUID, int]]:
        if feed_mode == 'subscriptions_only':
            author_ids = {viewer_user_id, *following_ids}
        elif feed_mode == 'subscribers_only':
            author_ids = {viewer_user_id, *follower_ids}
        else:
            author_ids = {viewer_user_id, *following_ids, *follower_ids}
        if not author_ids:
            return []
        q = (
            select(FeedPost.id, FeedPost.user_id)
            .where(FeedPost.user_id.in_(author_ids))
            .order_by(FeedPost.created_at.desc(), FeedPost.id.desc())
            .limit(const.feed.STREAM_POOL_LIMIT)
        )
        rows = (await self._session.execute(q)).all()
        # film_id placeholder -1: пост без привязки к фильму в антиспаме по фильму
        return [(int(r[0]), r[1], -1) for r in rows]

    async def _build_streams(
        self,
        *,
        viewer_user_id: UUID,
        following_ids: set[UUID],
        follower_ids: set[UUID],
        graph_user_ids: set[UUID],
        genre_profile: set[str],
        tag_profile: set[str],
        feed_mode: FeedMode,
    ) -> dict[const.feed.StreamName, list[tuple[int, UUID, int]]]:
        async def _ordered_cards(where_clause: Any) -> list[tuple[int, UUID, int]]:
            q = (
                select(UserCard.id, UserCard.user_id, UserCard.film_id)
                .where(where_clause)
                .order_by(UserCard.updated_at.desc(), UserCard.id.desc())
                .limit(const.feed.STREAM_POOL_LIMIT)
            )
            rows = (await self._session.execute(q)).all()
            out: list[tuple[int, UUID, int]] = []
            for r in rows:
                fid = r[2]
                tail_fid = int(fid) if fid is not None else -1
                out.append((int(r[0]), r[1], tail_fid))
            return out

        if following_ids:
            sub_cards = await _ordered_cards(UserCard.user_id.in_(following_ids))
        else:
            sub_cards = []

        if follower_ids:
            subr_cards = await _ordered_cards(UserCard.user_id.in_(follower_ids))
        else:
            subr_cards = []

        disc = await _ordered_cards(~UserCard.user_id.in_(graph_user_ids))

        affinity = await self._build_affinity_stream(viewer_user_id, genre_profile, tag_profile)

        feed_posts = await self._build_post_stream(
            viewer_user_id=viewer_user_id,
            following_ids=following_ids,
            follower_ids=follower_ids,
            feed_mode=feed_mode,
        )

        own_cards = await _ordered_cards(UserCard.user_id == viewer_user_id)

        return {
            'subscriptions': sub_cards,
            'subscribers': subr_cards,
            'personal_affinity': affinity,
            'discovery': disc,
            'feed_posts': feed_posts,
            'own_cards': own_cards,
        }

    async def _build_affinity_stream(
        self,
        viewer_user_id: UUID,
        genre_profile: set[str],
        tag_profile: set[str],
    ) -> list[tuple[int, UUID, int]]:
        q = (
            select(
                UserCard.id,
                UserCard.user_id,
                UserCard.film_id,
                Film.genres,
                UserCard.updated_at,
            )
            .join(Film, Film.id == UserCard.film_id)
            .where(UserCard.user_id != viewer_user_id)
            .order_by(UserCard.updated_at.desc(), UserCard.id.desc())
            .limit(const.feed.AFFINITY_CANDIDATE_SCAN)
        )
        rows = (await self._session.execute(q)).all()
        if not rows:
            return []

        card_ids = [int(r[0]) for r in rows]
        tags_by_card: dict[int, list[str]] = {c: [] for c in card_ids}
        tr = (
            await self._session.execute(
                select(CardTag.card_id, CardTag.tag).where(CardTag.card_id.in_(card_ids))
            )
        ).all()
        for cid, tag in tr:
            tags_by_card[int(cid)].append(tag)

        scored: list[tuple[int, int, UUID, int, dt.datetime | None]] = []
        for rid, uid, fid, genres, updated_at in rows:
            cid = int(rid)
            gfilm = {_norm_genre(str(g)) for g in (genres or [])}
            tc = {_norm_tag(t) for t in tags_by_card.get(cid, [])}
            g_overlap = len(genre_profile & gfilm)
            t_overlap = len(tag_profile & tc)
            score = (
                const.feed.GENRE_OVERLAP_WEIGHT * g_overlap
                + const.feed.TAG_OVERLAP_WEIGHT * t_overlap
            )
            scored.append((cid, score, uid, fid, updated_at))

        def sort_key(
            item: tuple[int, int, UUID, int, dt.datetime | None],
        ) -> tuple[int, float, int]:
            cid, score, _uid, _fid, updated_at = item
            ts = -updated_at.timestamp() if updated_at else 0.0
            return (-score, ts, -cid)

        scored.sort(key=sort_key)
        return [(x[0], x[2], x[3]) for x in scored[: const.feed.STREAM_POOL_LIMIT]]

    def _merge_feed(
        self,
        state: _MergeState,
        streams: dict[const.feed.StreamName, list[tuple[int, UUID, int]]],
        limit: int,
        viewer_user_id: UUID,
    ) -> tuple[list[tuple[Literal['card', 'post'], int, const.feed.StreamName]], _MergeState, bool]:
        """Состояние merge после ровно min(limit, доступно) выдач; has_more — есть ли ещё один кандидат."""
        working = state.clone()
        out: list[tuple[Literal['card', 'post'], int, const.feed.StreamName]] = []
        max_steps = max(5000, limit * 200)
        for _ in range(max_steps):
            if len(out) >= limit:
                break
            picked = self._pick_one_slot(streams, working, viewer_user_id)
            if picked is None:
                break
            out.append(picked)

        probe = working.clone()
        has_more = self._pick_one_slot(streams, probe, viewer_user_id) is not None
        return out, working, has_more

    def _pick_one_slot(
        self,
        streams: dict[const.feed.StreamName, list[tuple[int, UUID, int]]],
        st: _MergeState,
        viewer_user_id: UUID,
    ) -> tuple[Literal['card', 'post'], int, const.feed.StreamName] | None:
        primary = const.feed.SLOT_PATTERN[st.slot_index % len(const.feed.SLOT_PATTERN)]
        got = self._take_next_from_stream(primary, streams, st, viewer_user_id)
        if got is None:
            for fb in const.feed.FALLBACK_ORDER:
                if fb == primary:
                    continue
                got = self._take_next_from_stream(fb, streams, st, viewer_user_id)
                if got is not None:
                    break
        if got is None:
            return None

        stream_name, cid, uid, fid, _ = got
        is_post = stream_name == 'feed_posts'
        if is_post:
            st.seen_posts.add(cid)
        else:
            st.seen_cards.add(cid)
        st.tail_author_ids.append(str(uid))
        st.tail_linked_film_ids.append(fid)
        k = const.feed.ANTI_SPAM_WINDOW
        if len(st.tail_author_ids) > k:
            st.tail_author_ids = st.tail_author_ids[-k:]
            st.tail_linked_film_ids = st.tail_linked_film_ids[-k:]
        st.slot_index += 1
        kind: Literal['card', 'post'] = 'post' if is_post else 'card'
        return kind, cid, stream_name

    def _take_next_from_stream(
        self,
        stream_name: const.feed.StreamName,
        streams: dict[const.feed.StreamName, list[tuple[int, UUID, int]]],
        st: _MergeState,
        viewer_user_id: UUID,
    ) -> tuple[const.feed.StreamName, int, UUID, int, int] | None:
        stream = streams[stream_name]
        is_post = stream_name == 'feed_posts'
        seen = st.seen_posts if is_post else st.seen_cards
        i = st.offsets[stream_name]
        while i < len(stream):
            cid, uid, fid = stream[i]
            i += 1
            st.offsets[stream_name] = i
            if cid in seen:
                continue
            if self._violates_antispam(uid, fid, st, viewer_user_id):
                continue
            return stream_name, cid, uid, fid, i
        return None

    def _violates_antispam(
        self, uid: UUID, film_id: int, st: _MergeState, viewer_user_id: UUID
    ) -> bool:
        # Подряд несколько своих карточек — нормальный сценарий; не блокируем по автору/фильму.
        if uid == viewer_user_id:
            return False
        k = const.feed.ANTI_SPAM_WINDOW
        if k <= 0:
            return False
        ua = str(uid)
        if ua in st.tail_author_ids[-k:]:
            return True
        if film_id <= 0:
            return False
        tail = st.tail_linked_film_ids[-k:]
        return film_id in tail

    async def _load_card_rows_ordered(
        self, ordered_ids: list[int]
    ) -> list[tuple[UserCard, Film | None, Game | None, User]]:
        if not ordered_ids:
            return []
        film_pk = func.coalesce(UserCard.film_id, CatalogItem.film_id)
        q = (
            select(UserCard, Film, Game, User)
            .join(User, User.id == UserCard.user_id)
            .outerjoin(CatalogItem, CatalogItem.id == UserCard.catalog_item_id)
            .outerjoin(Film, Film.id == film_pk)
            .outerjoin(Game, Game.id == CatalogItem.game_id)
            .where(UserCard.id.in_(ordered_ids))
        )
        rows = (await self._session.execute(q)).all()
        by_id = {row[0].id: row for row in rows}
        return [by_id[i] for i in ordered_ids if i in by_id]

    async def _hydrate_feed_items(
        self,
        viewer_user_id: UUID,
        visible_rows: list[tuple[UserCard, Film | None, Game | None, User]],
        source_by_id: dict[int, const.feed.StreamName],
    ) -> list[UserCardFeedItem]:
        card_ids = [card.id for card, _film, _game, _author in visible_rows]

        cat_ids = list({int(c.category_id) for c, _f, _g, _a in visible_rows})
        cat_names: dict[int, str] = {}
        if cat_ids:
            for crow in (
                (
                    await self._session.execute(
                        select(UserCardCategory).where(UserCardCategory.id.in_(cat_ids))
                    )
                )
                .scalars()
                .all()
            ):
                cat_names[int(crow.id)] = crow.name

        tags_by_card: dict[int, list[str]] = {}
        if card_ids:
            tags_rows = (
                await self._session.execute(
                    select(CardTag.card_id, CardTag.tag)
                    .where(CardTag.card_id.in_(card_ids))
                    .order_by(CardTag.card_id, CardTag.tag)
                )
            ).all()
            for card_id_val, tag in tags_rows:
                tags_by_card.setdefault(int(card_id_val), []).append(tag)

        counts_by_card: dict[int, int] = dict.fromkeys(card_ids, 0)
        if card_ids:
            count_rows = (
                await self._session.execute(
                    select(CardComment.card_id, func.count(CardComment.id))
                    .where(CardComment.card_id.in_(card_ids))
                    .group_by(CardComment.card_id)
                )
            ).all()
            for card_id_val, cnt in count_rows:
                counts_by_card[int(card_id_val)] = int(cnt)

        previews_by_card: dict[int, list[UserCardCommentItem]] = {cid: [] for cid in card_ids}
        if card_ids:
            ranked = (
                select(
                    CardComment.id,
                    CardComment.card_id,
                    CardComment.user_id,
                    CardComment.parent_comment_id,
                    CardComment.text,
                    CardComment.image_url,
                    CardComment.created_at,
                    func.row_number()
                    .over(
                        partition_by=CardComment.card_id,
                        order_by=CardComment.id.desc(),
                    )
                    .label('rn'),
                ).where(CardComment.card_id.in_(card_ids))
            ).subquery()

            preview_stmt = (
                select(
                    ranked.c.id,
                    ranked.c.card_id,
                    ranked.c.parent_comment_id,
                    ranked.c.text,
                    ranked.c.image_url,
                    ranked.c.created_at,
                    User,
                )
                .join(User, User.id == ranked.c.user_id)
                .where(ranked.c.rn <= 3)
                .order_by(ranked.c.card_id.asc(), ranked.c.id.asc())
            )

            preview_rows = (await self._session.execute(preview_stmt)).all()
            for (
                cid,
                user_card_id,
                parent_comment_id,
                text,
                image_url,
                created_at,
                author_row,
            ) in preview_rows:
                previews_by_card[int(user_card_id)].append(
                    UserCardCommentItem(
                        id=int(cid),
                        user_card_id=int(user_card_id),
                        parent_comment_id=parent_comment_id,
                        text=text,
                        image_url=image_url,
                        created_at=created_at,
                        replies_count=0,
                        total_descendants_count=0,
                        author=UserCardCommentAuthor(
                            id=author_row.id,
                            profile_slug=author_row.profile_slug,
                            username=author_row.username,
                            first_name=author_row.first_name,
                            last_name=author_row.last_name,
                            photo_url=author_row.photo_url,
                            display_name=author_row.display_name,
                        ),
                        reactions=ReactionTargetSummary(counts=(), my_reaction_type_ids=()),
                    )
                )

        preview_comment_ids: list[int] = []
        for plist in previews_by_card.values():
            for p in plist:
                preview_comment_ids.append(p.id)

        card_summaries, comment_summaries, _, _ = await GetReactionSummariesForTargetsService(
            self._session
        ).execute(
            viewer_user_id=viewer_user_id,
            user_card_ids=card_ids,
            comment_ids=preview_comment_ids,
            feed_post_comment_ids=[],
            feed_post_ids=[],
        )

        flat_tmps: list[UserCardCommentItem] = []
        flat_card_ids: list[int] = []
        for card, _film, _game, _card_author_user in visible_rows:
            for p in previews_by_card.get(card.id, []):
                flat_tmps.append(
                    UserCardCommentItem(
                        id=p.id,
                        user_card_id=p.user_card_id,
                        parent_comment_id=p.parent_comment_id,
                        text=p.text,
                        image_url=p.image_url,
                        created_at=p.created_at,
                        replies_count=p.replies_count,
                        total_descendants_count=p.total_descendants_count,
                        author=p.author,
                        reactions=comment_summaries[p.id],
                    )
                )
                flat_card_ids.append(card.id)
        flat_pairs = [(t.author.id, t.text) for t in flat_tmps]
        if flat_pairs:
            ref_all, men_all = await batch_resolve_comment_inline_refs(self._session, flat_pairs)
        else:
            ref_all, men_all = [], []
        enriched_flat = [
            replace(
                flat_tmps[i],
                referenced_inline_user_cards=ref_all[i],
                referenced_mentions=men_all[i],
            )
            for i in range(len(flat_tmps))
        ]
        previews_resolved: dict[int, list[UserCardCommentItem]] = {cid: [] for cid in card_ids}
        for i, cid in enumerate(flat_card_ids):
            previews_resolved[cid].append(enriched_flat[i])

        items: list[UserCardFeedItem] = []
        for card, film, game, card_author_user in visible_rows:
            preview_with_rx = previews_resolved.get(card.id, [])
            display_title = (card.display_title or '').strip()
            if not display_title and film is not None:
                display_title = (film.title or '').strip()
            if not display_title:
                display_title = 'Untitled'
            film_title_dep = film.title if film is not None else display_title
            cid = int(card.category_id)
            film_year_val = film.year if film is not None else None
            release_year, release_date = universal_release_year_date(
                film_year=film_year_val,
                game_released=game.released if game is not None else None,
            )
            items.append(
                UserCardFeedItem(
                    id=card.id,
                    user_id=card.user_id,
                    card_author=UserCardCommentAuthor(
                        id=card_author_user.id,
                        profile_slug=card_author_user.profile_slug,
                        username=card_author_user.username,
                        first_name=card_author_user.first_name,
                        last_name=card_author_user.last_name,
                        photo_url=card_author_user.photo_url,
                        display_name=card_author_user.display_name,
                    ),
                    provider=card.provider,
                    external_id=card.external_id,
                    film_id=film.id if film is not None else None,
                    film_kinopoisk_id=film.kinopoisk_id if film is not None else None,
                    film_genres=list(film.genres or []) if film is not None else [],
                    film_title=film_title_dep,
                    film_year=film_year_val,
                    release_year=release_year,
                    release_date=release_date,
                    film_poster_url=film.poster_url if film is not None else None,
                    catalog_item_id=card.catalog_item_id,
                    display_title=display_title,
                    display_cover_url=card.display_cover_url,
                    display_summary=card.display_summary,
                    rating=float(card.rating),
                    company=card.company,
                    mood_before=card.mood_before,
                    mood_after=card.mood_after,
                    watch_note=card.watch_note or '',
                    custom_tags=tags_by_card.get(card.id, []),
                    comments_count=counts_by_card.get(card.id, 0),
                    comments_preview=preview_with_rx,
                    reactions=card_summaries[card.id],
                    feed_source=source_by_id[card.id],
                    is_favorite=bool(card.is_favorite),
                    is_planned=bool(card.is_planned),
                    category_id=cid,
                    category_name=cat_names.get(cid, DEFAULT_USER_CARD_CATEGORY_NAME),
                    audio_url=card.audio_url,
                )
            )
        return items

    async def _hydrate_feed_post_items(
        self,
        viewer_user_id: UUID,
        ordered_post_ids: list[int],
        source_by_id: dict[int, const.feed.StreamName],
    ) -> list[FeedPostFeedItem]:
        if not ordered_post_ids:
            return []
        rows = (
            await self._session.execute(
                select(FeedPost, User)
                .join(User, User.id == FeedPost.user_id)
                .where(FeedPost.id.in_(ordered_post_ids))
            )
        ).all()
        by_id = {int(fp.id): (fp, u) for fp, u in rows}

        pids = [pid for pid in ordered_post_ids if pid in by_id]
        counts_by_post, previews_by_post, fp_rx = await _load_feed_post_engagement_maps(
            self._session, viewer_user_id, pids
        )
        snap = FeedPostEngagementSnapshot(
            counts_by_post=counts_by_post,
            previews_by_post=previews_by_post,
            fp_reactions=fp_rx,
        )

        ref_cids = [int(fp.referenced_card_id) for fp, _ in by_id.values() if fp.referenced_card_id]
        ref_by_cid: dict[int, tuple[UserCard, Film | None, Game | None]] = {}
        if ref_cids:
            film_pk = func.coalesce(UserCard.film_id, CatalogItem.film_id)
            rq = (
                select(UserCard, Film, Game)
                .outerjoin(CatalogItem, CatalogItem.id == UserCard.catalog_item_id)
                .outerjoin(Film, Film.id == film_pk)
                .outerjoin(Game, Game.id == CatalogItem.game_id)
                .where(UserCard.id.in_(ref_cids))
            )
            for card, film, game in (await self._session.execute(rq)).all():
                ref_by_cid[int(card.id)] = (card, film, game)

        items: list[FeedPostFeedItem] = []
        for pid in ordered_post_ids:
            row = by_id.get(pid)
            if row is None:
                continue
            fp, author_user = row
            ref_snippet: FeedPostReferencedCardSnippet | None = None
            rid = fp.referenced_card_id
            if rid is not None and int(rid) in ref_by_cid:
                mc, fl, gm = ref_by_cid[int(rid)]
                ref_title = (
                    str(fl.title)
                    if fl is not None
                    else ((mc.display_title or '').strip() or 'Untitled')
                )
                fy = fl.year if fl is not None else None
                release_year, release_date = universal_release_year_date(
                    film_year=fy,
                    game_released=gm.released if gm is not None else None,
                )
                ref_poster = fl.poster_url if fl is not None else mc.display_cover_url
                ref_snippet = FeedPostReferencedCardSnippet(
                    user_card_id=int(mc.id),
                    film_title=ref_title,
                    film_year=fy,
                    release_year=release_year,
                    release_date=release_date,
                    film_poster_url=ref_poster,
                    rating=float(mc.rating),
                    is_planned=bool(mc.is_planned),
                )
            author = UserCardCommentAuthor(
                id=author_user.id,
                profile_slug=author_user.profile_slug,
                username=author_user.username,
                first_name=author_user.first_name,
                last_name=author_user.last_name,
                photo_url=author_user.photo_url,
                display_name=author_user.display_name,
            )
            fpid = int(fp.id)
            items.append(
                FeedPostFeedItem(
                    id=fpid,
                    user_id=fp.user_id,
                    author=author,
                    body=fp.body or '',
                    image_url=fp.image_url,
                    referenced_user_card_id=int(rid) if rid is not None else None,
                    source_comment_id=int(fp.source_comment_id)
                    if fp.source_comment_id is not None
                    else None,
                    created_at=fp.created_at,
                    feed_source=source_by_id[fpid],
                    referenced_card=ref_snippet,
                )
            )
        return await attach_feed_post_list_engagement(
            self._session, viewer_user_id, items, engagement=snap
        )

    async def hydrate_global_feed_user_cards(
        self,
        viewer_user_id: UUID,
        ordered_card_ids: list[int],
    ) -> list[UserCardFeedItem]:
        """Публичная глобальная лента: карточки с feed_source=global (без merge-потоков)."""
        if not ordered_card_ids:
            return []
        rows = await self._load_card_rows_ordered(ordered_card_ids)
        sources: dict[int, const.feed.StreamName] = dict.fromkeys(ordered_card_ids, 'global')
        return await self._hydrate_feed_items(viewer_user_id, rows, sources)

    async def hydrate_global_feed_posts(
        self,
        viewer_user_id: UUID,
        ordered_post_ids: list[int],
    ) -> list[FeedPostFeedItem]:
        if not ordered_post_ids:
            return []
        sources: dict[int, const.feed.StreamName] = dict.fromkeys(ordered_post_ids, 'global')
        return await self._hydrate_feed_post_items(viewer_user_id, ordered_post_ids, sources)
