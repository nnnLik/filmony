from __future__ import annotations

import base64
import datetime as dt
import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

import const.feed
from const.feed import FeedMode
from models.film import Film
from models.movie_card import MovieCard
from models.movie_card_comment import MovieCardComment
from models.movie_card_tag import MovieCardTag
from models.user import User
from models.user_subscription import UserSubscription
from services.cards.list_movie_card_comments import MovieCardCommentAuthor, MovieCardCommentItem
from services.reactions import GetReactionSummariesForTargetsService
from services.reactions.types import ReactionTargetSummary

CURSOR_PREFIX = 'v1.'


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
class MovieCardFeedItem:
    id: int
    user_id: UUID
    card_author: MovieCardCommentAuthor
    film_id: int
    film_kinopoisk_id: int
    film_genres: list[str]
    film_title: str
    film_year: int | None
    film_poster_url: str | None
    rating: float
    company: str
    mood_before: str
    mood_after: str
    custom_tags: list[str]
    comments_count: int
    comments_preview: list[MovieCardCommentItem]
    reactions: ReactionTargetSummary
    feed_source: const.feed.StreamName
    is_favorite: bool


@dataclass(frozen=True, slots=True)
class MovieCardFeedPage:
    items: list[MovieCardFeedItem]
    next_cursor: str | None


@dataclass
class _MergeState:
    offsets: dict[str, int]
    slot_index: int
    seen: set[int]
    tail_author_ids: list[str]
    tail_film_ids: list[int]
    feed_mode: FeedMode
    hide_own_cards: bool

    @classmethod
    def initial(
        cls, feed_mode: FeedMode = 'default', *, hide_own_cards: bool = False
    ) -> _MergeState:
        return cls(
            offsets=dict.fromkeys(const.feed.STREAM_KEYS, 0),
            slot_index=0,
            seen=set(),
            tail_author_ids=[],
            tail_film_ids=[],
            feed_mode=feed_mode,
            hide_own_cards=hide_own_cards,
        )

    @classmethod
    def from_cursor_payload(cls, data: dict[str, Any]) -> _MergeState | None:
        if data.get('v') != 1:
            return None
        offsets = _parse_cursor_offsets(data.get('offsets'))
        if offsets is None:
            return None
        seen_list = data.get('seen', [])
        if not isinstance(seen_list, list):
            return None
        seen = {int(x) for x in seen_list}
        ta = data.get('tail_authors', [])
        tf = data.get('tail_films', [])
        if not isinstance(ta, list) or not isinstance(tf, list):
            return None
        raw_mode = data.get('mode', 'default')
        if raw_mode not in const.feed.VALID_FEED_MODES:
            return None
        hide_raw = data.get('hide_own', False)
        hide_own_cards = bool(hide_raw) if isinstance(hide_raw, bool) else False
        return cls(
            offsets=offsets,
            slot_index=int(data.get('slot_index', 0)),
            seen=seen,
            tail_author_ids=[str(x) for x in ta],
            tail_film_ids=[int(x) for x in tf],
            feed_mode=raw_mode,
            hide_own_cards=hide_own_cards,
        )

    def to_payload(self) -> dict[str, Any]:
        seen_list = sorted(self.seen)
        cap = const.feed.FEED_CURSOR_SEEN_MAX
        if len(seen_list) > cap:
            seen_list = seen_list[-cap:]
        return {
            'v': 1,
            'offsets': {k: self.offsets[k] for k in const.feed.STREAM_KEYS},
            'slot_index': self.slot_index,
            'seen': seen_list,
            'tail_authors': list(self.tail_author_ids),
            'tail_films': list(self.tail_film_ids),
            'mode': self.feed_mode,
            'hide_own': self.hide_own_cards,
        }

    def clone(self) -> _MergeState:
        return _MergeState(
            offsets=dict(self.offsets),
            slot_index=self.slot_index,
            seen=set(self.seen),
            tail_author_ids=list(self.tail_author_ids),
            tail_film_ids=list(self.tail_film_ids),
            feed_mode=self.feed_mode,
            hide_own_cards=self.hide_own_cards,
        )


def _encode_cursor(state: _MergeState) -> str:
    raw = json.dumps(state.to_payload(), separators=(',', ':')).encode()
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
        data = json.loads(raw.decode('utf-8'))
    except (ValueError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    return _MergeState.from_cursor_payload(data)


class ListMovieCardFeedService:
    """Собирает персональную ленту карточек из нескольких потоков и возвращает источник каждой позиции."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(
        self,
        viewer_user_id: UUID,
        cursor: str | None,
        limit: int,
        *,
        feed_mode: FeedMode = 'default',
        hide_own_cards: bool = False,
    ) -> MovieCardFeedPage:
        decoded = _decode_cursor(cursor)
        if decoded is not None and (
            decoded.feed_mode != feed_mode or decoded.hide_own_cards != hide_own_cards
        ):
            merge_state = _MergeState.initial(feed_mode, hide_own_cards=hide_own_cards)
        elif decoded is not None:
            merge_state = decoded
        else:
            merge_state = _MergeState.initial(feed_mode, hide_own_cards=hide_own_cards)

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
        )
        streams = self._streams_for_mode(streams, feed_mode)
        if hide_own_cards:
            streams = {**streams, 'own': []}

        ordered_pairs, next_state, has_more = self._merge_feed(
            merge_state, streams, limit, viewer_user_id
        )

        ordered_ids = [p[0] for p in ordered_pairs]
        source_by_id = dict(ordered_pairs)

        visible_rows = await self._load_card_rows_ordered(ordered_ids)
        items = await self._hydrate_feed_items(viewer_user_id, visible_rows, source_by_id)

        next_cursor: str | None = _encode_cursor(next_state) if has_more else None
        return MovieCardFeedPage(items=items, next_cursor=next_cursor)

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
                .join(MovieCard, MovieCard.film_id == Film.id)
                .where(MovieCard.user_id == viewer_id)
            )
        ).all()
        gset: set[str] = set()
        for (glist,) in genres_rows:
            for g in glist or []:
                gset.add(_norm_genre(str(g)))

        tag_rows = (
            (
                await self._session.execute(
                    select(MovieCardTag.tag)
                    .join(MovieCard, MovieCard.id == MovieCardTag.movie_card_id)
                    .where(MovieCard.user_id == viewer_id)
                )
            )
            .scalars()
            .all()
        )
        tset = {_norm_tag(t) for t in tag_rows}
        return gset, tset

    async def _build_streams(
        self,
        *,
        viewer_user_id: UUID,
        following_ids: set[UUID],
        follower_ids: set[UUID],
        graph_user_ids: set[UUID],
        genre_profile: set[str],
        tag_profile: set[str],
    ) -> dict[const.feed.StreamName, list[tuple[int, UUID, int]]]:
        async def _ordered_cards(where_clause: Any) -> list[tuple[int, UUID, int]]:
            q = (
                select(MovieCard.id, MovieCard.user_id, MovieCard.film_id)
                .where(where_clause)
                .order_by(MovieCard.created_at.desc(), MovieCard.id.desc())
                .limit(const.feed.STREAM_POOL_LIMIT)
            )
            rows = (await self._session.execute(q)).all()
            return [(int(r[0]), r[1], int(r[2])) for r in rows]

        own = await _ordered_cards(MovieCard.user_id == viewer_user_id)

        if following_ids:
            sub_cards = await _ordered_cards(MovieCard.user_id.in_(following_ids))
        else:
            sub_cards = []

        if follower_ids:
            subr_cards = await _ordered_cards(MovieCard.user_id.in_(follower_ids))
        else:
            subr_cards = []

        disc = await _ordered_cards(~MovieCard.user_id.in_(graph_user_ids))

        affinity = await self._build_affinity_stream(viewer_user_id, genre_profile, tag_profile)

        return {
            'own': own,
            'subscriptions': sub_cards,
            'subscribers': subr_cards,
            'personal_affinity': affinity,
            'discovery': disc,
        }

    async def _build_affinity_stream(
        self,
        viewer_user_id: UUID,
        genre_profile: set[str],
        tag_profile: set[str],
    ) -> list[tuple[int, UUID, int]]:
        q = (
            select(
                MovieCard.id,
                MovieCard.user_id,
                MovieCard.film_id,
                Film.genres,
                MovieCard.created_at,
            )
            .join(Film, Film.id == MovieCard.film_id)
            .where(MovieCard.user_id != viewer_user_id)
            .order_by(MovieCard.created_at.desc(), MovieCard.id.desc())
            .limit(const.feed.AFFINITY_CANDIDATE_SCAN)
        )
        rows = (await self._session.execute(q)).all()
        if not rows:
            return []

        card_ids = [int(r[0]) for r in rows]
        tags_by_card: dict[int, list[str]] = {c: [] for c in card_ids}
        tr = (
            await self._session.execute(
                select(MovieCardTag.movie_card_id, MovieCardTag.tag).where(
                    MovieCardTag.movie_card_id.in_(card_ids)
                )
            )
        ).all()
        for cid, tag in tr:
            tags_by_card[int(cid)].append(tag)

        scored: list[tuple[int, int, UUID, int, dt.datetime | None]] = []
        for rid, uid, fid, genres, created_at in rows:
            cid = int(rid)
            gfilm = {_norm_genre(str(g)) for g in (genres or [])}
            tc = {_norm_tag(t) for t in tags_by_card.get(cid, [])}
            g_overlap = len(genre_profile & gfilm)
            t_overlap = len(tag_profile & tc)
            score = (
                const.feed.GENRE_OVERLAP_WEIGHT * g_overlap
                + const.feed.TAG_OVERLAP_WEIGHT * t_overlap
            )
            scored.append((cid, score, uid, fid, created_at))

        def sort_key(
            item: tuple[int, int, UUID, int, dt.datetime | None],
        ) -> tuple[int, float, int]:
            cid, score, _uid, _fid, created_at = item
            ts = -created_at.timestamp() if created_at else 0.0
            return (-score, ts, -cid)

        scored.sort(key=sort_key)
        return [(x[0], x[2], x[3]) for x in scored[: const.feed.STREAM_POOL_LIMIT]]

    def _merge_feed(
        self,
        state: _MergeState,
        streams: dict[const.feed.StreamName, list[tuple[int, UUID, int]]],
        limit: int,
        viewer_user_id: UUID,
    ) -> tuple[list[tuple[int, const.feed.StreamName]], _MergeState, bool]:
        """Состояние merge после ровно min(limit, доступно) выдач; has_more — есть ли ещё один кандидат."""
        working = state.clone()
        out: list[tuple[int, const.feed.StreamName]] = []
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
    ) -> tuple[int, const.feed.StreamName] | None:
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
        st.seen.add(cid)
        st.tail_author_ids.append(str(uid))
        st.tail_film_ids.append(fid)
        k = const.feed.ANTI_SPAM_WINDOW
        if len(st.tail_author_ids) > k:
            st.tail_author_ids = st.tail_author_ids[-k:]
            st.tail_film_ids = st.tail_film_ids[-k:]
        st.slot_index += 1
        return cid, stream_name

    def _take_next_from_stream(
        self,
        stream_name: const.feed.StreamName,
        streams: dict[const.feed.StreamName, list[tuple[int, UUID, int]]],
        st: _MergeState,
        viewer_user_id: UUID,
    ) -> tuple[const.feed.StreamName, int, UUID, int, int] | None:
        stream = streams[stream_name]
        i = st.offsets[stream_name]
        while i < len(stream):
            cid, uid, fid = stream[i]
            i += 1
            st.offsets[stream_name] = i
            if cid in st.seen:
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
        tail = st.tail_film_ids[-k:]
        return film_id in tail

    async def _load_card_rows_ordered(
        self, ordered_ids: list[int]
    ) -> list[tuple[MovieCard, Film, User]]:
        if not ordered_ids:
            return []
        q = (
            select(MovieCard, Film, User)
            .join(Film, Film.id == MovieCard.film_id)
            .join(User, User.id == MovieCard.user_id)
            .where(MovieCard.id.in_(ordered_ids))
        )
        rows = (await self._session.execute(q)).all()
        by_id = {row[0].id: row for row in rows}
        return [by_id[i] for i in ordered_ids if i in by_id]

    async def _hydrate_feed_items(
        self,
        viewer_user_id: UUID,
        visible_rows: list[tuple[MovieCard, Film, User]],
        source_by_id: dict[int, const.feed.StreamName],
    ) -> list[MovieCardFeedItem]:
        card_ids = [card.id for card, _film, _author in visible_rows]

        tags_by_card: dict[int, list[str]] = {}
        if card_ids:
            tags_rows = (
                await self._session.execute(
                    select(MovieCardTag.movie_card_id, MovieCardTag.tag)
                    .where(MovieCardTag.movie_card_id.in_(card_ids))
                    .order_by(MovieCardTag.movie_card_id, MovieCardTag.tag)
                )
            ).all()
            for card_id_val, tag in tags_rows:
                tags_by_card.setdefault(int(card_id_val), []).append(tag)

        counts_by_card: dict[int, int] = dict.fromkeys(card_ids, 0)
        if card_ids:
            count_rows = (
                await self._session.execute(
                    select(MovieCardComment.movie_card_id, func.count(MovieCardComment.id))
                    .where(MovieCardComment.movie_card_id.in_(card_ids))
                    .group_by(MovieCardComment.movie_card_id)
                )
            ).all()
            for card_id_val, cnt in count_rows:
                counts_by_card[int(card_id_val)] = int(cnt)

        previews_by_card: dict[int, list[MovieCardCommentItem]] = {cid: [] for cid in card_ids}
        if card_ids:
            ranked = (
                select(
                    MovieCardComment.id,
                    MovieCardComment.movie_card_id,
                    MovieCardComment.user_id,
                    MovieCardComment.parent_comment_id,
                    MovieCardComment.text,
                    MovieCardComment.created_at,
                    func.row_number()
                    .over(
                        partition_by=MovieCardComment.movie_card_id,
                        order_by=MovieCardComment.id.desc(),
                    )
                    .label('rn'),
                ).where(MovieCardComment.movie_card_id.in_(card_ids))
            ).subquery()

            preview_stmt = (
                select(
                    ranked.c.id,
                    ranked.c.movie_card_id,
                    ranked.c.parent_comment_id,
                    ranked.c.text,
                    ranked.c.created_at,
                    User,
                )
                .join(User, User.id == ranked.c.user_id)
                .where(ranked.c.rn <= 3)
                .order_by(ranked.c.movie_card_id.asc(), ranked.c.id.asc())
            )

            preview_rows = (await self._session.execute(preview_stmt)).all()
            for (
                cid,
                movie_card_id,
                parent_comment_id,
                text,
                created_at,
                author_row,
            ) in preview_rows:
                previews_by_card[int(movie_card_id)].append(
                    MovieCardCommentItem(
                        id=int(cid),
                        movie_card_id=int(movie_card_id),
                        parent_comment_id=parent_comment_id,
                        text=text,
                        created_at=created_at,
                        replies_count=0,
                        total_descendants_count=0,
                        author=MovieCardCommentAuthor(
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

        card_summaries, comment_summaries = await GetReactionSummariesForTargetsService(
            self._session
        ).execute(
            viewer_user_id=viewer_user_id,
            movie_card_ids=card_ids,
            comment_ids=preview_comment_ids,
        )

        items: list[MovieCardFeedItem] = []
        for card, film, card_author_user in visible_rows:
            prev_list = previews_by_card.get(card.id, [])
            preview_with_rx = [
                MovieCardCommentItem(
                    id=p.id,
                    movie_card_id=p.movie_card_id,
                    parent_comment_id=p.parent_comment_id,
                    text=p.text,
                    created_at=p.created_at,
                    replies_count=p.replies_count,
                    total_descendants_count=p.total_descendants_count,
                    author=p.author,
                    reactions=comment_summaries[p.id],
                )
                for p in prev_list
            ]
            items.append(
                MovieCardFeedItem(
                    id=card.id,
                    user_id=card.user_id,
                    card_author=MovieCardCommentAuthor(
                        id=card_author_user.id,
                        profile_slug=card_author_user.profile_slug,
                        username=card_author_user.username,
                        first_name=card_author_user.first_name,
                        last_name=card_author_user.last_name,
                        photo_url=card_author_user.photo_url,
                        display_name=card_author_user.display_name,
                    ),
                    film_id=film.id,
                    film_kinopoisk_id=film.kinopoisk_id,
                    film_genres=list(film.genres or []),
                    film_title=film.title,
                    film_year=film.year,
                    film_poster_url=film.poster_url,
                    rating=float(card.rating),
                    company=card.company,
                    mood_before=card.mood_before,
                    mood_after=card.mood_after,
                    custom_tags=tags_by_card.get(card.id, []),
                    comments_count=counts_by_card.get(card.id, 0),
                    comments_preview=preview_with_rx,
                    reactions=card_summaries[card.id],
                    feed_source=source_by_id[card.id],
                    is_favorite=bool(card.is_favorite),
                )
            )
        return items
