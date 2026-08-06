"""Pure logic tests for collection progress completion rules."""

from __future__ import annotations

import datetime as dt

import pytest

from services.collections.refresh_user_collection_progress import (
    resolve_completed_at,
    should_mark_collection_completed,
)


def test_should_mark_collection_completed_requires_nonzero_total() -> None:
    assert not should_mark_collection_completed(
        rated_count=0,
        total_count=0,
        completed_at=None,
    )
    assert not should_mark_collection_completed(
        rated_count=5,
        total_count=0,
        completed_at=None,
    )


def test_should_mark_collection_completed_when_all_rated() -> None:
    assert should_mark_collection_completed(
        rated_count=3,
        total_count=3,
        completed_at=None,
    )
    assert should_mark_collection_completed(
        rated_count=5,
        total_count=3,
        completed_at=None,
    )


def test_should_mark_collection_completed_false_when_already_completed() -> None:
    completed = dt.datetime(2026, 1, 1, tzinfo=dt.UTC)
    assert not should_mark_collection_completed(
        rated_count=3,
        total_count=3,
        completed_at=completed,
    )


def test_resolve_completed_at_sticky_after_first_completion() -> None:
    completed = dt.datetime(2026, 1, 1, 12, 0, tzinfo=dt.UTC)
    now = dt.datetime(2026, 6, 1, 12, 0, tzinfo=dt.UTC)

    assert (
        resolve_completed_at(
            rated_count=1,
            total_count=3,
            existing_completed_at=completed,
            now=now,
        )
        == completed
    )


def test_resolve_completed_at_sets_timestamp_on_first_completion() -> None:
    now = dt.datetime(2026, 6, 1, 12, 0, tzinfo=dt.UTC)

    assert (
        resolve_completed_at(
            rated_count=3,
            total_count=3,
            existing_completed_at=None,
            now=now,
        )
        == now
    )


def test_resolve_completed_at_none_while_in_progress() -> None:
    now = dt.datetime(2026, 6, 1, 12, 0, tzinfo=dt.UTC)

    assert (
        resolve_completed_at(
            rated_count=1,
            total_count=3,
            existing_completed_at=None,
            now=now,
        )
        is None
    )


@pytest.mark.parametrize(
    ('rated_count', 'total_count', 'expected'),
    [
        (0, 3, False),
        (2, 3, False),
        (3, 3, True),
        (4, 3, True),
    ],
)
def test_should_mark_collection_completed_parametrized(
    rated_count: int,
    total_count: int,
    expected: bool,
) -> None:
    assert (
        should_mark_collection_completed(
            rated_count=rated_count,
            total_count=total_count,
            completed_at=None,
        )
        is expected
    )
