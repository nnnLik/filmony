"""Removing a custom avatar restores the public Telegram userpic URL."""

from __future__ import annotations

import datetime as dt
from uuid import uuid4

import pytest

from models.user import User
from services.profile.clear_my_avatar import ClearMyAvatarService
from services.profile.resolve_telegram_avatar_url import ResolveTelegramAvatarUrlService
from utils.avatar_photo_url import custom_avatar_photo_url, telegram_userpic_url


class _Result:
    def __init__(self, user: User) -> None:
        self._user = user

    def scalar_one_or_none(self) -> User:
        return self._user


class _Session:
    def __init__(self, user: User) -> None:
        self.user = user
        self.commits = 0

    async def execute(self, _statement: object) -> _Result:
        return _Result(self.user)

    async def commit(self) -> None:
        self.commits += 1

    async def refresh(self, _user: User) -> None:
        return None


def _user(photo_url: str | None, username: str | None = 'alice') -> User:
    return User(
        id=uuid4(),
        telegram_user_id=15,
        username=username,
        first_name='Alice',
        last_name=None,
        photo_url=photo_url,
        profile_slug='alice',
        language_code='ru',
        updated_at=dt.datetime.now(dt.UTC),
    )


@pytest.mark.asyncio
async def test_clear_custom_avatar_uses_telegram_userpic(monkeypatch: pytest.MonkeyPatch) -> None:
    user = _user(custom_avatar_photo_url(uuid4(), 1))
    user.photo_url = custom_avatar_photo_url(user.id, 9)
    deleted: list[object] = []

    async def _delete(user_id: object) -> None:
        deleted.append(user_id)

    monkeypatch.setattr('services.profile.clear_my_avatar.delete_avatar_object', _delete)
    service = ClearMyAvatarService(
        _session=_Session(user),
        _resolve_telegram_avatar=ResolveTelegramAvatarUrlService(_bot=None),
    )

    updated = await service.execute(user.id)

    assert deleted == [user.id]
    assert updated.photo_url == telegram_userpic_url('alice')
    assert updated.photo_url != ''


@pytest.mark.asyncio
async def test_clear_is_noop_when_photo_is_already_telegram(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    telegram = telegram_userpic_url('alice')
    user = _user(telegram)

    async def _delete(_user_id: object) -> None:
        raise AssertionError('telegram photo must not delete an object')

    monkeypatch.setattr('services.profile.clear_my_avatar.delete_avatar_object', _delete)
    service = ClearMyAvatarService(
        _session=_Session(user),
        _resolve_telegram_avatar=ResolveTelegramAvatarUrlService(_bot=None),
    )

    updated = await service.execute(user.id)

    assert updated.photo_url == telegram
