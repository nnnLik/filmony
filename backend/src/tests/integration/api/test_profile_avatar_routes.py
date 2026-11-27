"""Custom avatar upload, replace, remove, and public media."""

from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient

from conf import settings
from core.rustfs_s3_client import RustfsGetObjectResult
from tests.auth.telegram_init_data import build_init_data

JPEG = b'\xff\xd8\xff\xe0' + b'\x00' * 16
PNG = b'\x89PNG\r\n\x1a\n' + b'\x00' * 16


class RecordingS3:
    def __init__(self) -> None:
        self.ops: list[tuple[str, str]] = []

    def delete_object(self, key: str) -> None:
        self.ops.append(('delete', key))

    def put_object(self, key: str, body: bytes, content_type: str) -> None:
        self.ops.append(('put', key))
        _ = body, content_type

    def get_object(self, key: str) -> RustfsGetObjectResult:
        _ = key
        return RustfsGetObjectResult(body=JPEG, content_type='image/jpeg')


def _install_s3(monkeypatch: pytest.MonkeyPatch, client: RecordingS3) -> None:
    monkeypatch.setattr(
        'services.profile.avatar_object_storage.RustfsS3Client.try_build_from_settings',
        lambda: client,
    )


async def _login(
    async_client: AsyncClient,
    telegram_user_id: int,
    *,
    photo_url: str | None = None,
) -> dict[str, object]:
    init = build_init_data(
        bot_token=settings.telegram.bot_token,
        user_id=telegram_user_id,
        photo_url=photo_url,
    )
    response = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, dict)
    return body


@pytest.mark.asyncio
async def test_avatar_upload_requires_auth(async_client: AsyncClient) -> None:
    response = await async_client.post(
        '/api/me/avatar',
        files={'file': ('a.jpg', JPEG, 'image/jpeg')},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_avatar_upload_rejects_empty_and_bad_type(async_client: AsyncClient) -> None:
    await _login(async_client, 880_001)
    empty = await async_client.post(
        '/api/me/avatar',
        files={'file': ('a.jpg', b'', 'image/jpeg')},
    )
    assert empty.status_code == 400

    wrong = await async_client.post(
        '/api/me/avatar',
        files={'file': ('a.jpg', PNG, 'image/jpeg')},
    )
    assert wrong.status_code == 400


@pytest.mark.asyncio
async def test_avatar_upload_replace_and_clear(
    monkeypatch: pytest.MonkeyPatch,
    async_client: AsyncClient,
) -> None:
    storage = RecordingS3()
    _install_s3(monkeypatch, storage)
    me = await _login(async_client, 880_002)
    user_id = str(me['id'])

    first = await async_client.post(
        '/api/me/avatar',
        files={'file': ('a.jpg', JPEG, 'image/jpeg')},
    )
    assert first.status_code == 200
    photo = first.json()['photo_url']
    assert isinstance(photo, str)
    assert photo.startswith(f'/api/users/avatar-media/user_media/avatars/{user_id}?v=')
    assert storage.ops == [('put', f'user_media/avatars/{user_id}')]

    second = await async_client.post(
        '/api/me/avatar',
        files={'file': ('b.png', PNG, 'image/png')},
    )
    assert second.status_code == 200
    replaced = second.json()['photo_url']
    assert isinstance(replaced, str)
    assert replaced.startswith(f'/api/users/avatar-media/user_media/avatars/{user_id}?v=')
    assert replaced != photo
    assert storage.ops[1:] == [
        ('delete', f'user_media/avatars/{user_id}'),
        ('put', f'user_media/avatars/{user_id}'),
    ]

    cleared = await async_client.delete('/api/me/avatar')
    assert cleared.status_code == 200
    restored = cleared.json()['photo_url']
    assert restored == 'https://t.me/i/userpic/320/tester.jpg'
    assert restored != ''
    assert storage.ops[-1] == ('delete', f'user_media/avatars/{user_id}')


@pytest.mark.asyncio
async def test_login_does_not_overwrite_custom_avatar(
    monkeypatch: pytest.MonkeyPatch,
    async_client: AsyncClient,
) -> None:
    _install_s3(monkeypatch, RecordingS3())
    await _login(async_client, 880_003)
    uploaded = await async_client.post(
        '/api/me/avatar',
        files={'file': ('a.jpg', JPEG, 'image/jpeg')},
    )
    assert uploaded.status_code == 200
    custom = uploaded.json()['photo_url']

    await _login(
        async_client,
        880_003,
        photo_url='https://cdn.example/telegram-fresh.jpg',
    )
    profile = await async_client.get('/api/me/profile')
    assert profile.status_code == 200
    assert profile.json()['photo_url'] == custom


@pytest.mark.asyncio
async def test_avatar_media_returns_bytes_and_rejects_foreign_prefix(
    monkeypatch: pytest.MonkeyPatch,
    async_client: AsyncClient,
) -> None:
    user_id = UUID('11111111-1111-4111-8111-111111111111')

    class _Reader:
        def get_object(self, key: str) -> RustfsGetObjectResult:
            assert key == f'user_media/avatars/{user_id}'
            return RustfsGetObjectResult(body=JPEG, content_type='image/jpeg')

    monkeypatch.setattr(
        'services.profile.get_avatar_media.RustfsS3Client.try_build_from_settings',
        _Reader,
    )
    ok = await async_client.get(f'/api/users/avatar-media/user_media/avatars/{user_id}')
    assert ok.status_code == 200
    assert ok.content == JPEG
    assert ok.headers['content-type'].startswith('image/jpeg')

    foreign = await async_client.get('/api/users/avatar-media/user_media/feed_posts/u/a.jpg')
    assert foreign.status_code == 404
