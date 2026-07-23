"""Tests for rich subscribed-activity digest message rendering."""

from __future__ import annotations

import datetime as dt
from uuid import uuid4

from services.telegram.build_subscribed_activity_digest_message import (
    BuildSubscribedActivityDigestMessageService,
    compute_digest_window_stats,
    render_digest_item_html,
)
from services.telegram.subscribed_activity_digest_candidates import (
    DigestCandidate,
    DigestCandidateKind,
)


def _card_candidate(
    *,
    kind: DigestCandidateKind = DigestCandidateKind.new_user_card,
    author_id=None,
    **kwargs,
) -> DigestCandidate:
    author = author_id or uuid4()
    defaults = {
        'kind': kind,
        'author_user_id': author,
        'author_display': 'Аня',
        'score': 100.0,
        'occurred_at': dt.datetime(2026, 7, 1, tzinfo=dt.UTC),
        'line_html': 'legacy',
        'entity_key': f'card:{uuid4().hex[:8]}',
        'card_id': 1,
        'film_title': 'Дюна',
        'film_year': 2021,
        'film_genres': ('фантастика', 'драма'),
        'tags': ('epic',),
        'rating': 9.0,
        'is_favorite': True,
        'mood_after': 'enjoyed',
    }
    defaults.update(kwargs)
    return DigestCandidate(**defaults)


def test_compute_window_stats_aggregates_genres_and_ratings() -> None:
    a1, a2 = uuid4(), uuid4()
    pool = [
        _card_candidate(author_id=a1, entity_key='card:1', card_id=1, rating=9.0),
        _card_candidate(
            author_id=a2,
            entity_key='card:2',
            card_id=2,
            film_title='Интерстellar',
            rating=8.0,
            is_favorite=False,
        ),
        DigestCandidate(
            kind=DigestCandidateKind.new_feed_post,
            author_user_id=a2,
            author_display='Макс',
            score=90.0,
            occurred_at=dt.datetime(2026, 7, 1, tzinfo=dt.UTC),
            line_html='legacy',
            entity_key='post:1',
            feed_post_id=1,
            post_snippet='Короткий пост',
        ),
    ]
    stats = compute_digest_window_stats(pool)
    assert stats.card_count == 2
    assert stats.post_count == 1
    assert stats.author_count == 2
    assert stats.avg_rating == 8.5
    assert stats.high_rating_count == 1
    assert stats.favorite_count == 1
    assert stats.top_genres[0][1] == 2
    assert {g for g, _ in stats.top_genres} == {'фантастика', 'драма'}


def test_render_new_user_card_includes_genres_rating_and_mood() -> None:
    html = render_digest_item_html(_card_candidate())
    assert '🎬' in html
    assert 'Аня' in html
    assert 'Дюна' in html
    assert '2021' in html
    assert '9/10' in html
    assert '⭐' in html
    assert 'фантастика' in html
    assert 'кайф' in html


def test_render_high_rating_card() -> None:
    html = render_digest_item_html(
        _card_candidate(kind=DigestCandidateKind.high_rating_card, entity_key='high:1')
    )
    assert '🔥' in html
    assert '9/10' in html
    assert 'фантастика' in html


def test_render_feed_post() -> None:
    html = render_digest_item_html(
        DigestCandidate(
            kind=DigestCandidateKind.new_feed_post,
            author_user_id=uuid4(),
            author_display='Макс',
            score=90.0,
            occurred_at=dt.datetime(2026, 7, 1, tzinfo=dt.UTC),
            line_html='legacy',
            entity_key='post:9',
            post_snippet='Наконец-то добрался до новой части',
        )
    )
    assert '💬' in html
    assert 'Макс' in html
    assert 'Наконец-то' in html


def test_render_author_summary_breaks_down_counts() -> None:
    html = render_digest_item_html(
        DigestCandidate(
            kind=DigestCandidateKind.author_activity_summary,
            author_user_id=uuid4(),
            author_display='Ирина',
            score=60.0,
            occurred_at=dt.datetime(2026, 7, 1, tzinfo=dt.UTC),
            line_html='legacy',
            entity_key='summary:x',
            activity_card_count=3,
            activity_post_count=1,
        )
    )
    assert '⚡' in html
    assert '3 карточки' in html
    assert '1 пост' in html


def test_build_message_includes_stats_intro_and_items() -> None:
    a1, a2 = uuid4(), uuid4()
    pool = [
        _card_candidate(author_id=a1, entity_key='card:1', card_id=1),
        _card_candidate(
            author_id=a2,
            entity_key='card:2',
            card_id=2,
            film_title='Барbie',
            rating=7.5,
            is_favorite=False,
        ),
    ]
    items = pool[:1]
    recipient = uuid4()
    window = dt.datetime(2026, 7, 1, 12, 0, tzinfo=dt.UTC)
    body = BuildSubscribedActivityDigestMessageService.build().execute(
        items=items,
        pool=pool,
        recipient_user_id=recipient,
        window_start=window,
    )
    assert '1.' in body
    assert 'Дюна' in body
    assert 'Открыть подборку в Filmony' in body
    assert any(marker in body for marker in ('🔔', '🎭', '⚡', '🔥', '⭐'))


def test_build_message_is_deterministic_for_same_seed() -> None:
    pool = [_card_candidate(entity_key='card:1', card_id=1)]
    recipient = uuid4()
    window = dt.datetime(2026, 7, 2, 8, 0, tzinfo=dt.UTC)
    svc = BuildSubscribedActivityDigestMessageService.build()
    first = svc.execute(
        items=pool,
        pool=pool,
        recipient_user_id=recipient,
        window_start=window,
    )
    second = svc.execute(
        items=pool,
        pool=pool,
        recipient_user_id=recipient,
        window_start=window,
    )
    assert first == second


def test_build_message_sparse_pool_uses_fallback_intro() -> None:
    pool = [
        DigestCandidate(
            kind=DigestCandidateKind.new_feed_post,
            author_user_id=uuid4(),
            author_display='Олег',
            score=90.0,
            occurred_at=dt.datetime(2026, 7, 1, tzinfo=dt.UTC),
            line_html='legacy',
            entity_key='post:1',
            post_snippet='Один пост',
        )
    ]
    body = BuildSubscribedActivityDigestMessageService.build().execute(
        items=pool,
        pool=pool,
        recipient_user_id=uuid4(),
        window_start=dt.datetime(2026, 7, 1, tzinfo=dt.UTC),
    )
    assert '🔔 Подборка за 48 часов' in body
    assert 'Олег' in body
