from __future__ import annotations

import datetime as dt

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from core.database import get_session_factory
from models.card_enums import CardCompany
from models.user import User
from models.user_card import UserCard
from models.user_subscription import UserSubscription
from models.watchlist_entry import WatchlistEntry
from services.watchlist.create_watchlist_entry import CreateWatchlistEntryService
from services.watchlist.update_watchlist_entry import UpdateWatchlistEntryService


async def _create_user(*, telegram_user_id: int, slug_suffix: str) -> User:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            telegram_user_id=telegram_user_id,
            profile_slug=f'wl-upd-{slug_suffix}',
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


async def _add_mutual_subscription(user_a: User, user_b: User) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(UserSubscription(follower_user_id=user_a.id, following_user_id=user_b.id))
        session.add(UserSubscription(follower_user_id=user_b.id, following_user_id=user_a.id))
        await session.commit()


@pytest.mark.asyncio
async def test_update_watchlist_entry_syncs_planned_card_metadata(
    async_client: AsyncClient,
) -> None:
    user = await _create_user(telegram_user_id=920000, slug_suffix='meta')
    created_at = dt.datetime(2026, 6, 30, 10, 0, 0, tzinfo=dt.UTC)
    session_factory = get_session_factory()
    async with session_factory() as session:
        create_service = CreateWatchlistEntryService.build(session)
        created = await create_service.execute(
            actor_user_id=user.id,
            card_id='kp:33333',
            provider_meta={'provider': 'kinopoisk', 'data': {'kp_id': 33333}},
            watch_tag='watch_later',
            company=CardCompany.alone,
            watch_note='old note',
            created_at=created_at,
        )
        entry_id = int(created.actor_entry.id)

        update_service = UpdateWatchlistEntryService.build(session)
        await update_service.execute(
            actor_user_id=user.id,
            entry_id=entry_id,
            company=CardCompany.friends,
            watch_note='updated note',
        )

    async with session_factory() as session:
        planned = (
            await session.execute(
                select(UserCard).where(
                    UserCard.user_id == user.id,
                    UserCard.is_planned.is_(True),
                )
            )
        ).scalar_one()
        assert planned.company == CardCompany.friends.value
        assert planned.watch_note == 'updated note'


@pytest.mark.asyncio
async def test_update_watchlist_entry_removes_invited_partner(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    import services.watchlist.create_watchlist_entry as create_watchlist_entry_module
    import services.watchlist.update_watchlist_entry as update_watchlist_entry_module

    actor = await _create_user(telegram_user_id=920001, slug_suffix='actor-rm')
    partner = await _create_user(telegram_user_id=920002, slug_suffix='partner-rm')
    await _add_mutual_subscription(actor, partner)
    created_at = dt.datetime(2026, 6, 30, 10, 0, 0, tzinfo=dt.UTC)

    class _FakeInviteService:
        async def execute(self, **kwargs) -> dict:
            return kwargs

    def _build_fake_invite_service() -> _FakeInviteService:
        return _FakeInviteService()

    monkeypatch.setattr(
        create_watchlist_entry_module.SendWatchlistInviteNotificationService,
        'build',
        _build_fake_invite_service,
    )
    monkeypatch.setattr(
        update_watchlist_entry_module.SendWatchlistInviteNotificationService,
        'build',
        _build_fake_invite_service,
    )

    session_factory = get_session_factory()
    async with session_factory() as session:
        create_service = CreateWatchlistEntryService.build(session)
        created = await create_service.execute(
            actor_user_id=actor.id,
            card_id='kp:22222',
            provider_meta={'provider': 'kinopoisk', 'data': {'kp_id': 22222}},
            watch_tag='watch_later',
            watch_with_user_id=partner.id,
            created_at=created_at,
        )
        entry_id = int(created.actor_entry.id)

        update_service = UpdateWatchlistEntryService.build(session)
        await update_service.execute(
            actor_user_id=actor.id,
            entry_id=entry_id,
            company=CardCompany.alone,
            watch_with_user_ids=[],
        )

    async with session_factory() as session:
        invite_entry = (
            await session.execute(
                select(WatchlistEntry).where(
                    WatchlistEntry.user_id == partner.id,
                    WatchlistEntry.card_id == 'kp:22222',
                )
            )
        ).scalar_one_or_none()
        assert invite_entry is None

        partner_planned = (
            await session.execute(
                select(UserCard).where(
                    UserCard.user_id == partner.id,
                    UserCard.is_planned.is_(True),
                )
            )
        ).scalar_one_or_none()
        assert partner_planned is None
