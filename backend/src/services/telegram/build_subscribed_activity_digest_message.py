"""Render rich Telegram HTML for subscribed-activity digest messages."""

from __future__ import annotations

import datetime as dt
import hashlib
import html
import random
from dataclasses import dataclass
from typing import Self
from uuid import UUID

from models.card_enums import CardMoodAfter
from services.telegram.mini_app_link import html_app_deep_link_block
from services.telegram.subscribed_activity_digest_candidates import (
    DigestCandidate,
    DigestCandidateKind,
)

_MOOD_AFTER_RU: dict[str, str] = {
    CardMoodAfter.laughed.value: 'весёлый',
    CardMoodAfter.cried.value: 'грустный',
    CardMoodAfter.enjoyed.value: 'кайф',
    CardMoodAfter.tense.value: 'уставший',
    CardMoodAfter.wasted_time.value: 'разочарование',
}


@dataclass(frozen=True, slots=True)
class DigestWindowStats:
    card_count: int
    post_count: int
    author_count: int
    avg_rating: float | None
    top_genres: tuple[tuple[str, int], ...]
    high_rating_count: int
    favorite_count: int


def compute_digest_window_stats(pool: list[DigestCandidate]) -> DigestWindowStats:
    card_kinds = {
        DigestCandidateKind.new_user_card,
        DigestCandidateKind.high_rating_card,
    }
    cards = [c for c in pool if c.kind in card_kinds]
    posts = [c for c in pool if c.kind == DigestCandidateKind.new_feed_post]

    unique_card_keys: set[str] = set()
    ratings: list[float] = []
    genre_counts: dict[str, int] = {}
    high_rating = 0
    favorites = 0

    for candidate in cards:
        key = f'card:{candidate.card_id}' if candidate.card_id is not None else candidate.entity_key
        if key in unique_card_keys:
            continue
        unique_card_keys.add(key)
        if candidate.rating is not None:
            ratings.append(float(candidate.rating))
            if candidate.rating >= 9.0:
                high_rating += 1
        if candidate.is_favorite:
            favorites += 1
        for genre in candidate.film_genres:
            g = genre.strip().lower()
            if g:
                genre_counts[g] = genre_counts.get(g, 0) + 1

    unique_post_keys = {c.entity_key for c in posts if c.kind == DigestCandidateKind.new_feed_post}
    authors = {
        c.author_user_id for c in pool if c.kind != DigestCandidateKind.author_activity_summary
    }

    top_genres = tuple(sorted(genre_counts.items(), key=lambda item: (-item[1], item[0]))[:3])
    avg_rating = round(sum(ratings) / len(ratings), 1) if ratings else None

    return DigestWindowStats(
        card_count=len(unique_card_keys),
        post_count=len(unique_post_keys),
        author_count=len(authors),
        avg_rating=avg_rating,
        top_genres=top_genres,
        high_rating_count=high_rating,
        favorite_count=favorites,
    )


def _deterministic_rng(*, recipient_user_id: UUID, window_start: dt.datetime) -> random.Random:
    seed_material = f'digest-intro:{recipient_user_id}:{window_start.isoformat()}'.encode()
    seed_int = int.from_bytes(hashlib.sha256(seed_material).digest()[:8], 'big')
    return random.Random(seed_int)


def _format_genres(genres: tuple[str, ...], *, max_items: int = 2) -> str:
    cleaned = [g.strip() for g in genres if g and g.strip()]
    if not cleaned:
        return ''
    shown = cleaned[:max_items]
    text = ', '.join(html.escape(g) for g in shown)
    if len(cleaned) > max_items:
        text += f' +{len(cleaned) - max_items}'
    return text


def _format_tags(tags: tuple[str, ...], *, max_items: int = 2) -> str:
    cleaned = [t.strip() for t in tags if t and t.strip()]
    if not cleaned:
        return ''
    shown = cleaned[:max_items]
    return ', '.join(html.escape(t) for t in shown)


def _title_html(candidate: DigestCandidate) -> str:
    raw = (candidate.film_title or 'Карточка').strip() or 'Карточка'
    return html.escape(raw)


def _mood_after_label(mood: str | None) -> str | None:
    if not mood:
        return None
    return _MOOD_AFTER_RU.get(mood, mood)


def _render_new_user_card(candidate: DigestCandidate) -> str:
    title = _title_html(candidate)
    year = f' ({candidate.film_year})' if candidate.film_year is not None else ''
    rating = f' — <b>{candidate.rating:.0f}/10</b>' if candidate.rating is not None else ''
    fav = ' ⭐' if candidate.is_favorite else ''
    genres = _format_genres(candidate.film_genres)
    tags = _format_tags(candidate.tags)

    detail_parts: list[str] = []
    if genres:
        detail_parts.append(f'🎭 {genres}')
    if tags:
        detail_parts.append(f'🏷 {tags}')
    mood = _mood_after_label(candidate.mood_after)
    if mood:
        detail_parts.append(f'после: {html.escape(mood)}')

    lines = [
        f'🎬 <b>{candidate.author_display}</b> — «{title}»{year}{rating}{fav}',
    ]
    if detail_parts:
        lines.append(f'   {" · ".join(detail_parts)}')
    return '\n'.join(lines)


def _render_high_rating_card(candidate: DigestCandidate) -> str:
    title = _title_html(candidate)
    rating = f'{candidate.rating:.0f}/10' if candidate.rating is not None else '9+/10'
    genres = _format_genres(candidate.film_genres)
    genre_suffix = f' · {genres}' if genres else ''
    fav = ' и в избранном' if candidate.is_favorite else ''
    return f'🔥 <b>{candidate.author_display}</b> поставил(а) {rating} «{title}»{fav}{genre_suffix}'


def _render_feed_post(candidate: DigestCandidate) -> str:
    snippet = candidate.post_snippet or '…'
    safe = html.escape(snippet)
    return f'💬 <b>{candidate.author_display}</b> в ленте: «{safe}»'


def _render_author_summary(candidate: DigestCandidate) -> str:
    parts: list[str] = []
    if candidate.activity_card_count:
        n = candidate.activity_card_count
        word = 'карточка' if n == 1 else ('карточки' if 2 <= n <= 4 else 'карточек')
        parts.append(f'{n} {word}')
    if candidate.activity_post_count:
        n = candidate.activity_post_count
        word = 'пост' if n == 1 else ('поста' if 2 <= n <= 4 else 'постов')
        parts.append(f'{n} {word}')
    joined = ' и '.join(parts) if parts else 'несколько событий'
    return f'⚡ <b>{candidate.author_display}</b> — {joined} за 48 ч'


def render_digest_item_html(candidate: DigestCandidate) -> str:
    if candidate.kind == DigestCandidateKind.new_user_card:
        return _render_new_user_card(candidate)
    if candidate.kind == DigestCandidateKind.high_rating_card:
        return _render_high_rating_card(candidate)
    if candidate.kind == DigestCandidateKind.new_feed_post:
        return _render_feed_post(candidate)
    if candidate.kind == DigestCandidateKind.author_activity_summary:
        return _render_author_summary(candidate)
    return candidate.line_html


def _build_intro_candidates(stats: DigestWindowStats) -> list[str]:
    candidates: list[str] = []

    if stats.top_genres and stats.card_count >= 2:
        top_name, top_count = stats.top_genres[0]
        genre_line = f'🎭 Тренд: <b>{html.escape(top_name)}</b> ({top_count}×)'
        if len(stats.top_genres) > 1:
            second_name, second_count = stats.top_genres[1]
            genre_line += f', {html.escape(second_name)} ({second_count}×)'
        if stats.avg_rating is not None:
            genre_line += f' · ср. оценка <b>{stats.avg_rating:.1f}/10</b>'
        candidates.append(genre_line)

    if stats.high_rating_count >= 2:
        candidates.append(
            f'🔥 <b>{stats.high_rating_count}</b> карточек с оценкой 9+ за 48 ч — вот самые яркие:'
        )

    total_events = stats.card_count + stats.post_count
    if total_events >= 4 and stats.author_count >= 2:
        candidates.append(
            f'⚡ <b>{total_events}</b> событий от <b>{stats.author_count}</b> авторов: '
            f'{stats.card_count} карточек, {stats.post_count} постов'
            + (
                f' · ср. оценка <b>{stats.avg_rating:.1f}/10</b>'
                if stats.avg_rating is not None
                else ''
            )
        )

    if stats.favorite_count >= 1 and stats.card_count >= 2:
        candidates.append(
            f'⭐ <b>{stats.favorite_count}</b> из {stats.card_count} новых карточек '
            f'попали в избранное у авторов'
        )

    candidates.append('🔔 Подборка за 48 часов от людей, на которых вы подписаны:')
    return candidates


def _pick_intro(
    *,
    stats: DigestWindowStats,
    recipient_user_id: UUID,
    window_start: dt.datetime,
) -> str:
    options = _build_intro_candidates(stats)
    if len(options) == 1:
        return options[0]
    rng = _deterministic_rng(
        recipient_user_id=recipient_user_id,
        window_start=window_start,
    )
    return rng.choice(options[:-1] if len(options) > 1 else options)


@dataclass
class BuildSubscribedActivityDigestMessageService:
    """Assembles HTML digest body with window stats and varied item formats."""

    @classmethod
    def build(cls) -> Self:
        return cls()

    def execute(
        self,
        *,
        items: list[DigestCandidate],
        pool: list[DigestCandidate],
        recipient_user_id: UUID,
        window_start: dt.datetime,
    ) -> str:
        stats = compute_digest_window_stats(pool)
        intro = _pick_intro(
            stats=stats,
            recipient_user_id=recipient_user_id,
            window_start=window_start,
        )

        lines = [intro, '']
        for idx, item in enumerate(items, start=1):
            rendered = render_digest_item_html(item)
            lines.append(f'{idx}. {rendered}')
            lines.append('')

        lines.append(html_app_deep_link_block(link_text='Открыть подборку в Filmony'))
        return '\n'.join(lines).rstrip()
