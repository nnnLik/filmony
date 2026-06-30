from __future__ import annotations

import datetime as dt
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from core.database import get_session_factory
from models.card_enums import CardCompany
from models.user import User
from models.user_card import UserCard
from models.user_card_category import UserCardCategory
from models.user_subscription import UserSubscription
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


async def _add_mutual_subscription(user_a: User, user_b: User) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(UserSubscription(follower_user_id=user_a.id, following_user_id=user_b.id))
        session.add(UserSubscription(follower_user_id=user_b.id, following_user_id=user_a.id))
        await session.commit()


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

    session_factory = get_session_factory()
    async with session_factory() as session:
        planned_card = (
            await session.execute(
                select(UserCard).where(
                    UserCard.user_id == user.id,
                    UserCard.is_planned.is_(True),
                )
            )
        ).scalar_one()
        assert planned_card.film_id is not None or planned_card.display_title


@pytest.mark.asyncio
async def test_create_watchlist_entry_creates_invited_entry(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    import services.watchlist.create_watchlist_entry as create_watchlist_entry_module

    actor = await _create_user(telegram_user_id=910001, slug_suffix='actor2')
    invited = await _create_user(telegram_user_id=910002, slug_suffix='invited')
    await _add_mutual_subscription(actor, invited)
    created_at = dt.datetime(2026, 6, 30, 9, 0, 0, tzinfo=dt.UTC)
    called: dict[str, object] = {}

    class _FakeInviteService:
        async def execute(
            self,
            *,
            actor_user_id,
            invited_user_id,
            planned_user_card_id,
            card_id,
        ) -> dict:
            called['actor_user_id'] = actor_user_id
            called['invited_user_id'] = invited_user_id
            called['planned_user_card_id'] = planned_user_card_id
            called['card_id'] = card_id
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


@pytest.mark.asyncio
async def test_create_watchlist_entry_rejects_non_mutual_watch_partner(
    async_client: AsyncClient,
) -> None:
    actor = await _create_user(telegram_user_id=910004, slug_suffix='actor-nonmutual')
    other = await _create_user(telegram_user_id=910005, slug_suffix='other-nonmutual')
    created_at = dt.datetime(2026, 6, 30, 9, 0, 0, tzinfo=dt.UTC)
    session_factory = get_session_factory()
    async with session_factory() as session:
        service = CreateWatchlistEntryService.build(session)
        with pytest.raises(CreateWatchlistEntryService.NotMutualWatchPartnerError):
            await service.execute(
                actor_user_id=actor.id,
                card_id='kp:88888',
                provider_meta={'provider': 'kinopoisk', 'data': {'kp_id': 88888}},
                watch_tag='watch_later',
                watch_with_user_id=other.id,
                created_at=created_at,
            )


@pytest.mark.asyncio
async def test_create_watchlist_entry_multi_invite(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    import services.watchlist.create_watchlist_entry as create_watchlist_entry_module

    actor = await _create_user(telegram_user_id=910160, slug_suffix='actor-multi')
    invited_a = await _create_user(telegram_user_id=910161, slug_suffix='invited-a')
    invited_b = await _create_user(telegram_user_id=910162, slug_suffix='invited-b')
    await _add_mutual_subscription(actor, invited_a)
    await _add_mutual_subscription(actor, invited_b)
    created_at = dt.datetime(2026, 6, 30, 9, 0, 0, tzinfo=dt.UTC)

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

    session_factory = get_session_factory()
    async with session_factory() as session:
        service = CreateWatchlistEntryService.build(session)
        result = await service.execute(
            actor_user_id=actor.id,
            card_id='kp:55555',
            provider_meta={'provider': 'kinopoisk', 'data': {'kp_id': 55555}},
            watch_tag='watch_later',
            company=CardCompany.friends,
            watch_note='note',
            watch_with_user_ids=[invited_a.id, invited_b.id],
            created_at=created_at,
        )

    assert result.actor_entry.watch_with_user_ids == [str(invited_a.id), str(invited_b.id)]
    assert len(result.invited_entries) == 2


@pytest.mark.asyncio
async def test_create_watchlist_entry_invitee_planned_card_uses_default_shelf(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    import services.watchlist.create_watchlist_entry as create_watchlist_entry_module

    actor = await _create_user(telegram_user_id=910170, slug_suffix='actor-cat')
    invited = await _create_user(telegram_user_id=910171, slug_suffix='invited-cat')
    await _add_mutual_subscription(actor, invited)
    created_at = dt.datetime(2026, 6, 30, 9, 0, 0, tzinfo=dt.UTC)

    session_factory = get_session_factory()
    async with session_factory() as session:
        actor_shelf = UserCardCategory(user_id=actor.id, name='Actor shelf only')
        session.add(actor_shelf)
        await session.commit()
        await session.refresh(actor_shelf)
        actor_category_id = int(actor_shelf.id)

    class _FakeInviteService:
        async def execute(self, **kwargs) -> dict:
            return kwargs

    monkeypatch.setattr(
        create_watchlist_entry_module.SendWatchlistInviteNotificationService,
        'build',
        _FakeInviteService,
    )

    async with session_factory() as session:
        service = CreateWatchlistEntryService.build(session)
        result = await service.execute(
            actor_user_id=actor.id,
            card_id='kp:44444',
            provider_meta={'provider': 'kinopoisk', 'data': {'kp_id': 44444}},
            watch_tag='watch_later',
            category_id=actor_category_id,
            watch_with_user_id=invited.id,
            created_at=created_at,
        )

    assert result.invited_entry is not None
    async with session_factory() as session:
        actor_planned = (
            await session.execute(
                select(UserCard).where(
                    UserCard.user_id == actor.id,
                    UserCard.is_planned.is_(True),
                )
            )
        ).scalar_one()
        invitee_planned = (
            await session.execute(
                select(UserCard).where(
                    UserCard.user_id == invited.id,
                    UserCard.is_planned.is_(True),
                )
            )
        ).scalar_one()
        assert int(actor_planned.category_id) == actor_category_id
        assert int(invitee_planned.category_id) != actor_category_id


@pytest.mark.asyncio
async def test_create_watchlist_entry_rejects_unknown_watch_with_user(
    async_client: AsyncClient,
) -> None:
    actor = await _create_user(telegram_user_id=910006, slug_suffix='actor-unknown')
    created_at = dt.datetime(2026, 6, 30, 9, 0, 0, tzinfo=dt.UTC)
    missing_user_id = UUID('f0000000-0000-4000-8000-000000000099')
    session_factory = get_session_factory()
    async with session_factory() as session:
        service = CreateWatchlistEntryService.build(session)
        with pytest.raises(CreateWatchlistEntryService.WatchWithUserNotFoundError):
            await service.execute(
                actor_user_id=actor.id,
                card_id='kp:77777',
                provider_meta={'provider': 'kinopoisk', 'data': {'kp_id': 77777}},
                watch_tag='watch_later',
                watch_with_user_id=missing_user_id,
                created_at=created_at,
            )
