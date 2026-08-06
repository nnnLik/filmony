"""Achievement pins HTTP API routes."""

from __future__ import annotations

from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from conf import settings
from core.database import get_session_factory
from models.achievement import Achievement
from models.collection import Collection, CollectionKind
from models.user import User
from models.user_achievement import UserAchievement
from models.user_achievement_pin import UserAchievementPin
from tests.auth.telegram_init_data import build_init_data


async def _login(async_client: AsyncClient, telegram_user_id: int) -> None:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    response = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert response.status_code == 200


async def _create_user(*, telegram_user_id: int) -> User:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            telegram_user_id=telegram_user_id,
            profile_slug=f'achapi-{telegram_user_id}',
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def _create_achievements(count: int, *, prefix: str) -> list[Achievement]:
    session_factory = get_session_factory()
    async with session_factory() as session:
        achievements: list[Achievement] = []
        for index in range(count):
            slug = f'{prefix}-{index}'
            collection = Collection(
                slug=slug,
                kind=CollectionKind.evergreen,
                title=f'Title {slug}',
                film_count=1,
            )
            session.add(collection)
            await session.flush()
            achievement = Achievement(
                slug=slug,
                collection_slug=slug,
                title=f'Achievement {slug}',
                description='desc',
            )
            session.add(achievement)
            achievements.append(achievement)
        await session.commit()
        for achievement in achievements:
            await session.refresh(achievement)
        return achievements


async def _unlock(user: User, achievement: Achievement) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(
            UserAchievement(
                user_id=user.id,
                achievement_id=int(achievement.id),
            )
        )
        await session.commit()


@pytest.mark.asyncio
async def test_list_my_achievements(async_client: AsyncClient) -> None:
    tg_id = 920001
    user = await _create_user(telegram_user_id=tg_id)
    achievements = await _create_achievements(2, prefix='ach-list')
    await _unlock(user, achievements[0])
    await _login(async_client, tg_id)

    response = await async_client.get('/api/me/achievements')
    assert response.status_code == 200
    payload = response.json()
    assert len(payload['items']) == 2
    unlocked = [item for item in payload['items'] if item['unlocked']]
    assert len(unlocked) == 1
    assert unlocked[0]['slug'] == achievements[0].slug


@pytest.mark.asyncio
async def test_set_achievement_pins_limit_and_public_profile(async_client: AsyncClient) -> None:
    tg_id = 920002
    user = await _create_user(telegram_user_id=tg_id)
    achievements = await _create_achievements(4, prefix='ach-pin')
    for achievement in achievements[:3]:
        await _unlock(user, achievement)
    await _login(async_client, tg_id)

    ok = await async_client.put(
        '/api/me/achievement-pins',
        json={'achievement_slugs': [achievements[0].slug, achievements[1].slug]},
    )
    assert ok.status_code == 204

    profile = await async_client.get(f'/api/users/{user.id}')
    assert profile.status_code == 200
    pinned = profile.json()['pinned_achievements']
    assert len(pinned) == 2
    assert pinned[0]['slug'] == achievements[0].slug
    assert pinned[1]['slug'] == achievements[1].slug

    too_many = await async_client.put(
        '/api/me/achievement-pins',
        json={'achievement_slugs': [a.slug for a in achievements[:4]]},
    )
    assert too_many.status_code == 422

    locked = await async_client.put(
        '/api/me/achievement-pins',
        json={'achievement_slugs': [achievements[3].slug]},
    )
    assert locked.status_code == 400

    missing = await async_client.put(
        '/api/me/achievement-pins',
        json={'achievement_slugs': ['does-not-exist']},
    )
    assert missing.status_code == 404


@pytest.mark.asyncio
async def test_clear_achievement_pins(async_client: AsyncClient) -> None:
    tg_id = 920003
    user = await _create_user(telegram_user_id=tg_id)
    achievements = await _create_achievements(1, prefix='ach-clear')
    await _unlock(user, achievements[0])
    await _login(async_client, tg_id)

    assert (
        await async_client.put(
            '/api/me/achievement-pins',
            json={'achievement_slugs': [achievements[0].slug]},
        )
    ).status_code == 204

    assert (
        await async_client.put('/api/me/achievement-pins', json={'achievement_slugs': []})
    ).status_code == 204

    session_factory = get_session_factory()
    async with session_factory() as session:
        count = int(
            (
                await session.execute(
                    select(UserAchievementPin).where(UserAchievementPin.user_id == user.id)
                )
            )
            .scalars()
            .all()
            .__len__()
        )
        assert count == 0

    missing_user = await async_client.get(f'/api/users/{uuid4()}')
    assert missing_user.status_code == 404
