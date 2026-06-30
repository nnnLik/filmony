from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from core.database import get_session_factory
from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from models.user import User
from models.user_card import UserCard
from services.telegram.send_watchlist_invite_notification import (
    SendWatchlistInviteNotificationService,
)
from tests.support.user_card_category import ensure_default_category


async def _create_user(
    *, telegram_user_id: int, slug_suffix: str, display_name: str | None = None
) -> User:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            telegram_user_id=telegram_user_id,
            profile_slug=f'wlinvite-{slug_suffix}',
            username=None,
            first_name='Test',
            last_name='User',
            photo_url=None,
            display_name=display_name,
            bio=None,
            language_code=None,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def _create_planned_card(*, user_id: UUID, film: Film) -> UserCard:
    session_factory = get_session_factory()
    async with session_factory() as session:
        cat_id = await ensure_default_category(session, user_id)
        card = UserCard(
            user_id=user_id,
            film_id=film.id,
            category_id=cat_id,
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
            rating=0.0,
            company='friends',
            mood_before='relax',
            mood_after='enjoyed',
            watch_note='Смотрим вечером',
            is_planned=True,
            display_title=film.title,
            display_cover_url=film.poster_url,
        )
        session.add(card)
        await session.commit()
        await session.refresh(card)
        return card


async def _create_film(*, kinopoisk_id: int = 930_123, title: str = 'Invite Film') -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title=title,
            year=2024,
            poster_url='https://example.com/invite.jpg',
            genres=['драма'],
        )
        session.add(film)
        await session.flush()
        session.add(
            CatalogItem(
                provider=CatalogProvider.kinopoisk,
                external_id=str(kinopoisk_id),
                film_id=film.id,
            )
        )
        await session.commit()
        await session.refresh(film)
        return film


@pytest.mark.asyncio
async def test_invite_notification_payload(
    async_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    actor = await _create_user(
        telegram_user_id=930001, slug_suffix='actor', display_name='Actor One'
    )
    invited = await _create_user(telegram_user_id=930002, slug_suffix='invited')
    film = await _create_film()
    planned_card = await _create_planned_card(user_id=invited.id, film=film)
    sent: dict[str, object] = {}

    async def _fake_send_photo(
        chat_id: int, poster: str, caption: str, *, parse_mode: str = 'HTML'
    ) -> None:
        sent['chat_id'] = chat_id
        sent['body'] = caption
        sent['poster'] = poster

    class _FakeSendService:
        @classmethod
        def build(cls) -> _FakeSendService:
            return cls()

        async def send_photo(
            self, chat_id: int, poster: str, caption: str, *, parse_mode: str = 'HTML'
        ) -> None:
            await _fake_send_photo(chat_id, poster, caption, parse_mode=parse_mode)

    monkeypatch.setattr(
        'services.telegram.send_watchlist_invite_notification.SendTelegramBotMessageService',
        _FakeSendService,
    )

    service = SendWatchlistInviteNotificationService.build()
    payload = await service.execute(
        actor_user_id=actor.id,
        invited_user_id=invited.id,
        planned_user_card_id=int(planned_card.id),
        card_id=f'kp:{film.kinopoisk_id}',
    )

    assert payload['user_id'] == invited.id
    assert payload['title'] == 'Приглашение посмотреть вместе'
    assert str(planned_card.id) in payload['deeplink']
    assert sent['chat_id'] == invited.telegram_user_id
    body = str(sent['body'])
    assert 'Actor One' in body
    assert 'Invite Film' in body
    assert 'Открыть запланированную карточку' in body
    assert 'Смотрим вечером' in body
