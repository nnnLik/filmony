from __future__ import annotations

import datetime as dt

import pytest
from httpx import AsyncClient

from core.database import get_session_factory
from models.user import User
from services.watchlist.create_watchlist_entry import CreateWatchlistEntryService


async def _create_user(*, telegram_user_id: int, slug_suffix: str) -> User:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            telegram_user_id=telegram_user_id,
            profile_slug=f'wl-{slug_suffix}',
            username=None,
            first_name=None,
            last_name=None,
            photo_url=None,
            display_name=None,
            bio=None,
            language_code=None,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


@pytest.mark.asyncio
async def test_create_watchlist_entry_persists_provider_meta(
    async_client: AsyncClient,
) -> None:
    user = await _create_user(telegram_user_id=910000, slug_suffix='actor')
    created_at = dt.datetime(2026, 6, 30, 9, 0, 0, tzinfo=dt.UTC)
    session_factory = get_session_factory()
    async with session_factory() as session:
        service = CreateWatchlistEntryService.build(session)
        result = await service.execute(
            actor_user_id=user.id,
            card_id='kp:12345',
            provider_meta={'provider': 'kinopoisk', 'data': {'kp_id': 12345}},
            watch_tag='watch_later',
            watch_with_user_id=None,
            created_at=created_at,
        )

    entry = result.actor_entry
    assert entry.user_id == user.id
    assert entry.card_id == 'kp:12345'
    assert entry.provider_meta['provider'] == 'kinopoisk'


@pytest.mark.asyncio
async def test_create_watchlist_entry_creates_invited_entry(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    import services.watchlist.create_watchlist_entry as create_watchlist_entry_module

    actor = await _create_user(telegram_user_id=910001, slug_suffix='actor2')
    invited = await _create_user(telegram_user_id=910002, slug_suffix='invited')
    created_at = dt.datetime(2026, 6, 30, 9, 0, 0, tzinfo=dt.UTC)
    called: dict[str, object] = {}

    class _FakeInviteService:
        async def execute(
            self,
            *,
            actor_user_id,
            invited_user_id,
            card_id,
            provider_meta,
        ) -> dict:
            called['actor_user_id'] = actor_user_id
            called['invited_user_id'] = invited_user_id
            called['card_id'] = card_id
            called['provider_meta'] = provider_meta
            return {}

    def _build_fake_invite_service() -> _FakeInviteService:
        return _FakeInviteService()

    monkeypatch.setattr(
        create_watchlist_entry_module.SendWatchlistInviteNotificationService,
        'build',
        _build_fake_invite_service,
    )

    session_factory = get_session_factory()
    async with session_factory() as session:
        service = CreateWatchlistEntryService.build(session)
        result = await service.execute(
            actor_user_id=actor.id,
            card_id='rawg:elden-ring',
            provider_meta={'provider': 'rawg', 'data': {'slug': 'elden-ring'}},
            watch_tag='watch_later',
            watch_with_user_id=invited.id,
            created_at=created_at,
        )

    assert result.actor_entry.user_id == actor.id
    assert result.invited_entry is not None
    assert result.invited_entry.user_id == invited.id
    assert result.invited_entry.card_id == 'rawg:elden-ring'
    assert called['invited_user_id'] == invited.id


@pytest.mark.asyncio
async def test_create_watchlist_entry_duplicate_raises_conflict(
    async_client: AsyncClient,
) -> None:
    user = await _create_user(telegram_user_id=910003, slug_suffix='duplicate')
    created_at = dt.datetime(2026, 6, 30, 9, 0, 0, tzinfo=dt.UTC)
    session_factory = get_session_factory()
    async with session_factory() as session:
        service = CreateWatchlistEntryService.build(session)
        await service.execute(
            actor_user_id=user.id,
            card_id='kp:99999',
            provider_meta={'provider': 'kinopoisk', 'data': {'kp_id': 99999}},
            watch_tag='watch_later',
            watch_with_user_id=None,
            created_at=created_at,
        )

        with pytest.raises(CreateWatchlistEntryService.WatchlistEntryAlreadyExistsError):
            await service.execute(
                actor_user_id=user.id,
                card_id='kp:99999',
                provider_meta={'provider': 'kinopoisk', 'data': {'kp_id': 99999}},
                watch_tag='watch_later',
                watch_with_user_id=None,
                created_at=created_at,
            )
