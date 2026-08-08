"""Monthly personal digest send idempotency."""

from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import UUID

import pytest
from sqlalchemy import select

from core.database import get_session_factory
from models.catalog_item import CatalogProvider
from models.film import Film
from models.personal_digest_delivery_state import PersonalDigestDeliveryState
from models.user import User
from models.user_card import UserCard
from services.personal_digest.send_personal_digest_telegram import (
    DigestDeliveryOutcome,
    SendPersonalDigestTelegramService,
)
from tests.support.user_card_category import ensure_default_category


async def _seed_monthly_digest_user(*, telegram_user_id: int) -> UUID:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            telegram_user_id=telegram_user_id,
            profile_slug=f'digest-{telegram_user_id}',
        )
        session.add(user)
        await session.flush()
        film = Film(
            kinopoisk_id=9_800_000 + telegram_user_id,
            title='Digest Film',
            year=2024,
            poster_url='https://example.com/poster.jpg',
            genres=['драма'],
            countries=['США'],
        )
        session.add(film)
        await session.flush()
        category_id = await ensure_default_category(session, user.id)
        session.add(
            UserCard(
                user_id=user.id,
                film_id=film.id,
                category_id=category_id,
                provider=CatalogProvider.kinopoisk,
                external_id=str(film.kinopoisk_id),
                rating=8.5,
                company='alone',
                mood_before='relax',
                mood_after='enjoyed',
                is_planned=False,
                completed_at=datetime(2026, 7, 15, 12, 0, tzinfo=UTC),
            )
        )
        await session.commit()
        return user.id


@pytest.mark.asyncio
async def test_send_monthly_digest_is_idempotent(
    prepare_db: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from conf import settings

    monkeypatch.setattr(settings.telegram, 'bot_username', 'stubfilmony_bot')
    user_id = await _seed_monthly_digest_user(telegram_user_id=9_810_001)

    mock_send = AsyncMock(return_value=None)
    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = SendPersonalDigestTelegramService.build(session)
        svc._send_svc.execute = mock_send
        first = await svc.execute(recipient_user_id=user_id, year=2026, month=7)
        second = await svc.execute(recipient_user_id=user_id, year=2026, month=7)

    assert first.outcome == DigestDeliveryOutcome.sent
    assert second.outcome == DigestDeliveryOutcome.skipped_already_sent
    assert mock_send.await_count == 1

    async with session_factory() as session:
        state = (
            await session.execute(
                select(PersonalDigestDeliveryState).where(
                    PersonalDigestDeliveryState.user_id == user_id,
                    PersonalDigestDeliveryState.period == 'month',
                    PersonalDigestDeliveryState.period_key == '2026-07',
                )
            )
        ).scalar_one()
        assert state.sent_at is not None
        assert state.payload_hash is not None
