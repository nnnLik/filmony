"""Login keeps a custom avatar URL and still refreshes the Telegram photo otherwise."""

from __future__ import annotations

import datetime as dt
from uuid import uuid4

import pytest

from models.user import User
from services.auth.dto import TelegramWebAppUser
from services.auth.upsert_telegram_user import UpsertTelegramUserService
from utils.avatar_photo_url import custom_avatar_photo_url


class _Result:
    def __init__(self, user: User | None) -> None:
        self._user = user

    def scalar_one_or_none(self) -> User | None:
        return self._user


class _Session:
    def __init__(self, user: User | None) -> None:
        self.user = user

    async def execute(self, _statement: object) -> _Result:
        return _Result(self.user)

    async def commit(self) -> None:
        return None

    async def refresh(self, _user: User) -> None:
        return None


def _user(*, photo_url: str | None) -> User:
    return User(
        id=uuid4(),
        telegram_user_id=77,
        username='old_name',
        first_name='Old',
        last_name=None,
        photo_url=photo_url,
        profile_slug='slugold',
        language_code='ru',
        updated_at=dt.datetime.now(dt.UTC),
    )


def _profile(*, photo_url: str) -> TelegramWebAppUser:
    return TelegramWebAppUser(
        telegram_user_id=77,
        username='new_name',
        first_name='New',
        last_name='User',
        photo_url=photo_url,
        language_code='en',
    )


@pytest.mark.asyncio
async def test_upsert_keeps_custom_avatar_photo_url() -> None:
    custom = custom_avatar_photo_url(uuid4(), 1)
    user = _user(photo_url=custom)
    user_id = user.id
    custom_for_user = custom_avatar_photo_url(user_id, 5)
    user.photo_url = custom_for_user

    updated = await UpsertTelegramUserService(_Session(user)).execute(
        _profile(photo_url='https://t.me/i/userpic/320/new_name.jpg'),
    )

    assert updated.photo_url == custom_for_user
    assert updated.username == 'new_name'
    assert updated.first_name == 'New'


@pytest.mark.asyncio
async def test_upsert_writes_telegram_photo_when_avatar_is_not_custom() -> None:
    user = _user(photo_url='https://t.me/i/userpic/320/old_name.jpg')
    incoming = 'https://t.me/i/userpic/320/new_name.jpg'

    updated = await UpsertTelegramUserService(_Session(user)).execute(
        _profile(photo_url=incoming),
    )

    assert updated.photo_url == incoming
