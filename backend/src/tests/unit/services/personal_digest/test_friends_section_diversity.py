"""Tests for weekly friends digest line selection diversity."""

from __future__ import annotations

from uuid import uuid4

from services.personal_digest.build_personal_digest_friends_section import (
    BuildPersonalDigestFriendsSectionService,
)


def _candidate(author_id, score: float, entity_key: str):
    from services.personal_digest.build_personal_digest_friends_section import _FriendCandidate

    return _FriendCandidate(
        author_user_id=author_id,
        score=score,
        line_text=f'line-{entity_key}',
        entity_key=entity_key,
    )


def test_select_diverse_caps_at_three_and_one_per_author() -> None:
    svc = BuildPersonalDigestFriendsSectionService(_session=None)
    author_a = uuid4()
    author_b = uuid4()
    author_c = uuid4()
    author_d = uuid4()
    candidates = [
        _candidate(author_a, 100.0, 'a1'),
        _candidate(author_a, 90.0, 'a2'),
        _candidate(author_b, 80.0, 'b1'),
        _candidate(author_c, 70.0, 'c1'),
        _candidate(author_d, 60.0, 'd1'),
    ]
    selected = svc._select_diverse(candidates, limit=3)
    assert len(selected) == 3
    selected_authors = {item.author_user_id for item in candidates if item.entity_key in selected}
    assert len(selected_authors) == 3
    assert author_a in selected_authors
    assert 'a1' in selected
    assert 'a2' not in selected


def test_select_diverse_allows_up_to_eight_in_app() -> None:
    svc = BuildPersonalDigestFriendsSectionService(_session=None)
    authors = [uuid4() for _ in range(10)]
    candidates = [
        _candidate(author_id, float(100 - index), f'k{index}')
        for index, author_id in enumerate(authors)
    ]
    selected = svc._select_diverse(candidates, limit=8)
    assert len(selected) == 8
