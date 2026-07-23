"""Subscribed-activity digest: candidate selection, delivery, and state."""

from __future__ import annotations

import datetime as dt
from unittest.mock import AsyncMock
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from core.database import get_session_factory
from models.catalog_item import CatalogProvider
from models.feed_post import FeedPost
from models.film import Film
from models.subscribed_activity_digest_state import SubscribedActivityDigestState
from models.user import User
from models.user_card import UserCard
from models.user_subscription import UserSubscription
from services.telegram.send_subscribed_activity_digest import (
    DigestDeliveryOutcome,
    SendSubscribedActivityTelegramDigestService,
)
from services.telegram.subscribed_activity_digest_candidates import (
    DigestCandidate,
    DigestCandidateKind,
    SelectSubscribedActivityDigestItemsService,
    digest_payload_hash,
)
from tests.support.user_card_category import ensure_default_category


def _candidate(
    *,
    kind: DigestCandidateKind,
    author_id: UUID,
    score: float,
    key: str,
) -> DigestCandidate:
    return DigestCandidate(
        kind=kind,
        author_user_id=author_id,
        author_display='Author',
        score=score,
        occurred_at=dt.datetime.now(tz=dt.UTC),
        line_html=f'<b>Author</b> event {key}',
        entity_key=key,
    )


def test_select_items_respects_one_per_author_cap() -> None:
    a1, a2, a3 = uuid4(), uuid4(), uuid4()
    pool = [
        _candidate(kind=DigestCandidateKind.new_user_card, author_id=a1, score=100, key='c1'),
        _candidate(kind=DigestCandidateKind.new_feed_post, author_id=a1, score=95, key='p1'),
        _candidate(kind=DigestCandidateKind.new_user_card, author_id=a2, score=90, key='c2'),
        _candidate(kind=DigestCandidateKind.new_feed_post, author_id=a3, score=85, key='p2'),
    ]
    window = dt.datetime(2026, 7, 1, tzinfo=dt.UTC)
    recipient = uuid4()
    selected = SelectSubscribedActivityDigestItemsService.build().execute(
        pool=pool,
        recipient_user_id=recipient,
        window_start=window,
    )
    assert len(selected) == 3
    authors = {c.author_user_id for c in selected}
    assert len(authors) == 3


def test_select_items_is_deterministic_for_same_seed() -> None:
    a1, a2, a3, a4 = uuid4(), uuid4(), uuid4(), uuid4()
    pool = [
        _candidate(kind=DigestCandidateKind.new_user_card, author_id=a1, score=100, key='c1'),
        _candidate(kind=DigestCandidateKind.new_user_card, author_id=a2, score=99, key='c2'),
        _candidate(kind=DigestCandidateKind.new_feed_post, author_id=a3, score=98, key='p1'),
        _candidate(kind=DigestCandidateKind.new_feed_post, author_id=a4, score=97, key='p2'),
    ]
    window = dt.datetime(2026, 7, 1, 12, 0, tzinfo=dt.UTC)
    recipient = uuid4()
    svc = SelectSubscribedActivityDigestItemsService.build()
    first = svc.execute(pool=pool, recipient_user_id=recipient, window_start=window)
    second = svc.execute(pool=pool, recipient_user_id=recipient, window_start=window)
    assert [c.entity_key for c in first] == [c.entity_key for c in second]


async def _seed_digest_fixture() -> tuple[UUID, UUID, int]:
    recipient = uuid4()
    author = uuid4()
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add_all(
            [
                User(
                    id=recipient,
                    telegram_user_id=9_520_001,
                    profile_slug=f'dgr{recipient.hex[:8]}',
                    display_name='Digest Recipient',
                ),
                User(
                    id=author,
                    telegram_user_id=9_520_002,
                    profile_slug=f'dga{author.hex[:8]}',
                    display_name='Digest Author',
                ),
            ]
        )
        session.add(UserSubscription(follower_user_id=recipient, following_user_id=author))
        film = Film(
            kinopoisk_id=9_520_101,
            title='Digest Film',
            year=2024,
            poster_url='https://example.com/p.jpg',
            genres=['drama'],
        )
        session.add(film)
        await session.flush()
        cat_id = await ensure_default_category(session, author)
        card = UserCard(
            user_id=author,
            film_id=film.id,
            category_id=cat_id,
            provider=CatalogProvider.kinopoisk,
            external_id='9520101',
            rating=9.5,
            company='alone',
            mood_before='relax',
            mood_after='enjoyed',
            is_favorite=True,
        )
        session.add(card)
        await session.flush()
        session.add(
            FeedPost(
                user_id=author,
                body='Digest post snippet for followers',
            )
        )
        await session.commit()
        return recipient, author, int(card.id)


@pytest.mark.asyncio
async def test_send_digest_delivers_three_insights(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from conf import settings

    monkeypatch.setattr(settings.telegram, 'bot_username', 'stubfilmony_bot')
    recipient, _author, _card_id = await _seed_digest_fixture()

    mock_send = AsyncMock(return_value=None)
    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = SendSubscribedActivityTelegramDigestService.build(session)
        svc._send_svc.execute = mock_send
        result = await svc.execute(recipient_user_id=recipient)

    assert result.outcome == DigestDeliveryOutcome.sent
    mock_send.assert_awaited_once()
    _chat_id, html_body = mock_send.await_args.args
    assert int(_chat_id) == 9_520_001
    assert 'Digest Film' in html_body
    assert 'Digest post snippet' in html_body
    assert any(marker in html_body for marker in ('🎬', '💬', '🔥', '⚡', '🎭', '🔔'))
    assert 'Открыть подборку в Filmony' in html_body

    async with session_factory() as session:
        state = (
            await session.execute(
                select(SubscribedActivityDigestState).where(
                    SubscribedActivityDigestState.recipient_user_id == recipient
                )
            )
        ).scalar_one()
        assert state.last_digest_sent_at is not None
        assert state.last_processed_at is not None
        assert state.last_digest_payload_hash is not None


@pytest.mark.asyncio
async def test_send_digest_skips_when_no_candidates(
    async_client: AsyncClient,
) -> None:
    recipient = uuid4()
    author = uuid4()
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add_all(
            [
                User(
                    id=recipient,
                    telegram_user_id=9_520_010,
                    profile_slug=f'dgn{recipient.hex[:8]}',
                ),
                User(
                    id=author,
                    telegram_user_id=9_520_011,
                    profile_slug=f'dgo{author.hex[:8]}',
                ),
            ]
        )
        session.add(UserSubscription(follower_user_id=recipient, following_user_id=author))
        await session.commit()

    mock_send = AsyncMock(return_value=None)
    async with session_factory() as session:
        svc = SendSubscribedActivityTelegramDigestService.build(session)
        svc._send_svc.execute = mock_send
        result = await svc.execute(recipient_user_id=recipient)

    assert result.outcome == DigestDeliveryOutcome.skipped_no_candidates
    mock_send.assert_not_awaited()


@pytest.mark.asyncio
async def test_send_digest_not_redelivered_within_processed_window(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from conf import settings

    monkeypatch.setattr(settings.telegram, 'bot_username', 'stubfilmony_bot')
    recipient, _, _ = await _seed_digest_fixture()

    mock_send = AsyncMock(return_value=None)
    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = SendSubscribedActivityTelegramDigestService.build(session)
        svc._send_svc.execute = mock_send
        first = await svc.execute(recipient_user_id=recipient)
        second = await svc.execute(recipient_user_id=recipient)

    assert first.outcome == DigestDeliveryOutcome.sent
    assert second.outcome == DigestDeliveryOutcome.skipped_no_candidates
    assert mock_send.await_count == 1


def test_digest_payload_hash_stable() -> None:
    items = [
        _candidate(
            kind=DigestCandidateKind.new_user_card,
            author_id=uuid4(),
            score=1,
            key='a',
        )
    ]
    assert digest_payload_hash(items) == digest_payload_hash(items)
