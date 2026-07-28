from __future__ import annotations

import datetime as dt
import random
from uuid import UUID

import pytest
from sqlalchemy import select

import celery_app
from core.database import get_session_factory
from models.card_enums import CardCompany, CardMoodAfter, CardMoodBefore
from models.catalog_item import CatalogProvider
from models.feed_post import FeedPost
from models.film import Film
from models.user import User
from models.user_card import UserCard
from models.user_subscription import UserSubscription
from models.watch_session import WatchSession
from models.watch_session_enums import WatchSessionStatus
from services.cards.create_user_card import CreateUserCardInput, CreateUserCardService
from services.feed_posts.get_feed_post_feed_item import GetFeedPostFeedItemService
from services.watch_sessions.create_coview_feed_post import CO_VIEW_FEED_POST_BODY
from services.watch_sessions.create_watch_session import CreateWatchSessionService
from services.watch_sessions.finalize_watch_session_if_ready import (
    FINALIZE_TIMEOUT,
    FinalizeWatchSessionIfReadyService,
)
from services.watch_sessions.record_watch_session_rating import RecordWatchSessionRatingService
from services.watchlist.create_watchlist_entry import CreateWatchlistEntryService
from tests.support.user_card_category import ensure_default_category


def _patch_fake_invite_service(monkeypatch: pytest.MonkeyPatch) -> None:
    import services.watchlist.create_watchlist_entry as create_watchlist_entry_module

    class _FakeInviteService:
        async def execute(self, **_: object) -> dict:
            return {}

    def _build_fake_invite_service() -> _FakeInviteService:
        return _FakeInviteService()

    monkeypatch.setattr(
        create_watchlist_entry_module.SendWatchlistInviteNotificationService,
        'build',
        _build_fake_invite_service,
    )


def _patch_noop_finalize_task(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        celery_app.app.tasks['tasks.watch_session.finalize_watch_session_if_ready'],
        'delay',
        lambda *_args, **_kwargs: None,
    )


async def _finalize_watch_session(watch_session_id: UUID) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        await FinalizeWatchSessionIfReadyService.build(session).execute(
            watch_session_id=watch_session_id,
        )


@pytest.fixture
def celery_always_eager() -> None:
    app = celery_app.app
    prev_eager = app.conf.task_always_eager
    prev_prop = app.conf.task_eager_propagates
    app.conf.task_always_eager = True
    app.conf.task_eager_propagates = True
    yield
    app.conf.task_always_eager = prev_eager
    app.conf.task_eager_propagates = prev_prop


async def _create_user(*, slug: str, telegram_user_id: int | None = None) -> User:
    tg_id = telegram_user_id if telegram_user_id is not None else random.randint(930_000_000, 939_999_999)
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            telegram_user_id=tg_id,
            profile_slug=slug,
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


async def _create_film(*, kinopoisk_id: int = 801_001) -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title='Co-view Film',
            year=2024,
            poster_url='https://example.com/coview.jpg',
            genres=['драма'],
        )
        session.add(film)
        await session.commit()
        await session.refresh(film)
        return film


async def _add_mutual_subscription(user_a: User, user_b: User) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(UserSubscription(follower_user_id=user_a.id, following_user_id=user_b.id))
        session.add(UserSubscription(follower_user_id=user_b.id, following_user_id=user_a.id))
        await session.commit()


async def _setup_coview_watchlist(
    *,
    actor: User,
    partner: User,
    film: Film,
) -> WatchSession:
    created_at = dt.datetime(2026, 7, 1, 12, 0, 0, tzinfo=dt.UTC)
    session_factory = get_session_factory()
    async with session_factory() as session:
        service = CreateWatchlistEntryService.build(session)
        await service.execute(
            actor_user_id=actor.id,
            card_id=f'kp:{film.kinopoisk_id}',
            provider_meta={'provider': 'kinopoisk', 'data': {'kp_id': film.kinopoisk_id}},
            watch_tag='watch_later',
            watch_with_user_ids=[partner.id],
            company=CardCompany.friends,
            created_at=created_at,
        )
        watch_session = (
            await session.execute(
                select(WatchSession).where(WatchSession.initiator_user_id == actor.id)
            )
        ).scalar_one()
        return watch_session


async def _rate_planned_card(
    *,
    user_id: UUID,
    film: Film,
    rating: float,
) -> UserCard:
    session_factory = get_session_factory()
    async with session_factory() as session:
        service = CreateUserCardService(session)
        card = await service.execute(
            user_id,
            CreateUserCardInput(
                film_id=int(film.id),
                kinopoisk_id=int(film.kinopoisk_id),
                rating=rating,
                company=CardCompany.friends,
                mood_before=CardMoodBefore.relax,
                mood_after=CardMoodAfter.enjoyed,
                custom_tags=[],
                watch_note='',
            ),
        )
        return card


@pytest.mark.asyncio
async def test_create_watchlist_with_partners_creates_planned_watch_session(
    prepare_db: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_fake_invite_service(monkeypatch)

    actor = await _create_user(slug='coview-actor')
    partner = await _create_user(slug='coview-partner')
    await _add_mutual_subscription(actor, partner)
    film = await _create_film(kinopoisk_id=801_010)

    session = await _setup_coview_watchlist(actor=actor, partner=partner, film=film)

    assert session.status == WatchSessionStatus.planned
    assert session.initiator_user_id == actor.id
    assert session.anchor_film_id == int(film.id)
    assert session.anchor_catalog_item_id is None
    assert [str(actor.id), str(partner.id)] == session.participant_user_ids


@pytest.mark.asyncio
async def test_record_rating_sets_first_rated_at(
    prepare_db: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_fake_invite_service(monkeypatch)
    _patch_noop_finalize_task(monkeypatch)

    actor = await _create_user(slug='coview-rate-a')
    partner = await _create_user(slug='coview-rate-b')
    await _add_mutual_subscription(actor, partner)
    film = await _create_film(kinopoisk_id=801_011)
    watch_session = await _setup_coview_watchlist(actor=actor, partner=partner, film=film)

    await _rate_planned_card(user_id=actor.id, film=film, rating=8.0)

    session_factory = get_session_factory()
    async with session_factory() as session:
        refreshed = await session.get(WatchSession, watch_session.id)
        assert refreshed is not None
        assert refreshed.first_rated_at is not None


@pytest.mark.asyncio
async def test_finalize_all_rated_creates_coview_feed_post(
    prepare_db: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_fake_invite_service(monkeypatch)
    _patch_noop_finalize_task(monkeypatch)

    actor = await _create_user(slug='coview-final-a')
    partner = await _create_user(slug='coview-final-b')
    await _add_mutual_subscription(actor, partner)
    film = await _create_film(kinopoisk_id=801_020)
    watch_session = await _setup_coview_watchlist(actor=actor, partner=partner, film=film)

    actor_card = await _rate_planned_card(user_id=actor.id, film=film, rating=7.5)
    await _rate_planned_card(user_id=partner.id, film=film, rating=9.0)
    await _finalize_watch_session(watch_session.id)

    session_factory = get_session_factory()
    async with session_factory() as session:
        refreshed = await session.get(WatchSession, watch_session.id)
        assert refreshed is not None
        assert refreshed.status == WatchSessionStatus.done
        assert refreshed.feed_post_id is not None

        post = await session.get(FeedPost, refreshed.feed_post_id)
        assert post is not None
        assert post.body == CO_VIEW_FEED_POST_BODY
        assert post.user_id == actor.id
        assert post.referenced_card_id == int(actor_card.id)
        assert post.watch_session_id == watch_session.id


@pytest.mark.asyncio
async def test_finalize_is_idempotent(prepare_db: None) -> None:
    actor = await _create_user(slug='coview-idem-a')
    partner = await _create_user(slug='coview-idem-b')
    film = await _create_film(kinopoisk_id=801_030)

    session_factory = get_session_factory()
    async with session_factory() as session:
        actor_category_id = await ensure_default_category(session, actor.id)
        partner_category_id = await ensure_default_category(session, partner.id)
        watch_session = await CreateWatchSessionService.build(session).execute(
            initiator_user_id=actor.id,
            partner_user_ids=[partner.id],
            anchor_film_id=int(film.id),
            anchor_catalog_item_id=None,
            source_watchlist_entry_id=None,
        )
        watch_session.first_rated_at = dt.datetime.now(tz=dt.UTC) - FINALIZE_TIMEOUT
        watch_session_id = watch_session.id

        actor_card = UserCard(
            user_id=actor.id,
            film_id=film.id,
            category_id=actor_category_id,
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
            rating=8.0,
            company=CardCompany.friends.value,
            mood_before=CardMoodBefore.relax.value,
            mood_after=CardMoodAfter.enjoyed.value,
            watch_note='',
            is_planned=False,
            completed_at=dt.datetime.now(tz=dt.UTC),
        )
        partner_card = UserCard(
            user_id=partner.id,
            film_id=film.id,
            category_id=partner_category_id,
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
            rating=7.0,
            company=CardCompany.friends.value,
            mood_before=CardMoodBefore.relax.value,
            mood_after=CardMoodAfter.enjoyed.value,
            watch_note='',
            is_planned=False,
            completed_at=dt.datetime.now(tz=dt.UTC),
        )
        session.add_all([actor_card, partner_card])
        await session.commit()

        finalize = FinalizeWatchSessionIfReadyService.build(session)
        assert await finalize.execute(watch_session_id=watch_session_id) is True
        first_post_id = (await session.get(WatchSession, watch_session_id)).feed_post_id
        assert await finalize.execute(watch_session_id=watch_session_id) is False

        post_count = (
            await session.execute(select(FeedPost).where(FeedPost.watch_session_id == watch_session_id))
        ).scalars().all()
        assert len(post_count) == 1
        assert first_post_id == post_count[0].id


@pytest.mark.asyncio
async def test_finalize_timeout_with_two_rated_creates_post(prepare_db: None) -> None:
    actor = await _create_user(slug='coview-timeout-a')
    partner = await _create_user(slug='coview-timeout-b')
    guest = await _create_user(slug='coview-timeout-c')
    film = await _create_film(kinopoisk_id=801_040)

    session_factory = get_session_factory()
    async with session_factory() as session:
        actor_category_id = await ensure_default_category(session, actor.id)
        partner_category_id = await ensure_default_category(session, partner.id)
        watch_session = await CreateWatchSessionService.build(session).execute(
            initiator_user_id=actor.id,
            partner_user_ids=[partner.id, guest.id],
            anchor_film_id=int(film.id),
            anchor_catalog_item_id=None,
            source_watchlist_entry_id=None,
        )
        watch_session.first_rated_at = dt.datetime.now(tz=dt.UTC) - FINALIZE_TIMEOUT - dt.timedelta(hours=1)
        watch_session_id = watch_session.id

        for user_id, rating, category_id in (
            (actor.id, 8.0, actor_category_id),
            (partner.id, 6.5, partner_category_id),
        ):
            session.add(
                UserCard(
                    user_id=user_id,
                    film_id=film.id,
                    category_id=category_id,
                    provider=CatalogProvider.kinopoisk,
                    external_id=str(film.kinopoisk_id),
                    rating=rating,
                    company=CardCompany.friends.value,
                    mood_before=CardMoodBefore.relax.value,
                    mood_after=CardMoodAfter.enjoyed.value,
                    watch_note='',
                    is_planned=False,
                    completed_at=dt.datetime.now(tz=dt.UTC),
                )
            )
        await session.commit()

        assert (
            await FinalizeWatchSessionIfReadyService.build(session).execute(
                watch_session_id=watch_session_id,
            )
            is True
        )
        refreshed = await session.get(WatchSession, watch_session_id)
        assert refreshed is not None
        assert refreshed.status == WatchSessionStatus.done
        assert refreshed.feed_post_id is not None
        assert refreshed.nudge_sent_at is not None


@pytest.mark.asyncio
async def test_feed_post_feed_item_includes_co_view_splits(
    prepare_db: None,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_fake_invite_service(monkeypatch)
    _patch_noop_finalize_task(monkeypatch)

    actor = await _create_user(slug='coview-feed-a')
    partner = await _create_user(slug='coview-feed-b')
    await _add_mutual_subscription(actor, partner)
    film = await _create_film(kinopoisk_id=801_050)
    watch_session = await _setup_coview_watchlist(actor=actor, partner=partner, film=film)

    await _rate_planned_card(user_id=actor.id, film=film, rating=7.0)
    await _rate_planned_card(user_id=partner.id, film=film, rating=8.5)
    await _finalize_watch_session(watch_session.id)

    session_factory = get_session_factory()
    async with session_factory() as session:
        finalized = await session.get(WatchSession, watch_session.id)
        assert finalized is not None
        assert finalized.feed_post_id is not None

        item = await GetFeedPostFeedItemService.build(session).execute(
            int(finalized.feed_post_id),
            actor.id,
        )
        assert len(item.co_view_splits) == 2
        by_user = {split.user_id: split for split in item.co_view_splits}
        assert by_user[actor.id].profile_slug == 'coview-feed-a'
        assert by_user[actor.id].rating == 7.0
        assert by_user[partner.id].profile_slug == 'coview-feed-b'
        assert by_user[partner.id].rating == 8.5
