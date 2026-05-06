from uuid import uuid4

import pytest
from httpx import AsyncClient

from conf import settings
from tests.auth.telegram_init_data import build_init_data


async def _login(async_client: AsyncClient, telegram_user_id: int) -> dict[str, object]:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    r = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert r.status_code == 200
    return r.json()


@pytest.mark.asyncio
async def test_my_profile_requires_auth(async_client: AsyncClient) -> None:
    r = await async_client.get('/api/me/profile')
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_my_profile_returns_slug_and_counts(async_client: AsyncClient) -> None:
    data = await _login(async_client, telegram_user_id=502)
    r = await async_client.get('/api/me/profile')
    assert r.status_code == 200
    body = r.json()
    assert body['id'] == data['id']
    assert body['profile_slug']
    assert body['profile_slug'].startswith('u')
    assert body['cards_count'] == 0
    assert body['friends_count'] == 0


@pytest.mark.asyncio
async def test_patch_my_profile_text_fields(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=503)
    r = await async_client.patch(
        '/api/me/profile',
        json={'display_name': '  Киноценз  ', 'bio': 'Люблю артхаус '},
    )
    assert r.status_code == 200
    assert r.json()['display_name'] == 'Киноценз'
    assert r.json()['bio'] == 'Люблю артхаус'

    cleared = await async_client.patch(
        '/api/me/profile',
        json={'display_name': None, 'bio': None},
    )
    assert cleared.status_code == 200
    assert cleared.json()['display_name'] is None
    assert cleared.json()['bio'] is None


@pytest.mark.asyncio
async def test_patch_my_profile_slug(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=504)
    r = await async_client.patch('/api/me/profile', json={'profile_slug': 'good-slug-4u'})
    assert r.status_code == 200
    assert r.json()['profile_slug'] == 'good-slug-4u'


@pytest.mark.asyncio
async def test_patch_my_profile_invalid_slug(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=505)
    r = await async_client.patch('/api/me/profile', json={'profile_slug': 'NO'})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_patch_my_profile_slug_conflict(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=506)
    r1 = await async_client.patch('/api/me/profile', json={'profile_slug': 'taken-slug-506'})
    assert r1.status_code == 200

    await _login(async_client, telegram_user_id=507)
    r2 = await async_client.patch('/api/me/profile', json={'profile_slug': 'taken-slug-506'})
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_patch_my_profile_rejects_unknown_field(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=508)
    r = await async_client.patch('/api/me/profile', json={'hacker_field': 'x'})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_public_profile_by_id_and_slug(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=509)
    await async_client.patch('/api/me/profile', json={'profile_slug': 'public-509'})

    await _login(async_client, telegram_user_id=510)

    by_id = await async_client.get(f'/api/users/{me["id"]}')
    assert by_id.status_code == 200
    assert by_id.json()['profile_slug'] == 'public-509'
    assert 'telegram_user_id' not in by_id.json()

    by_slug = await async_client.get('/api/users/by-slug/public-509')
    assert by_slug.status_code == 200
    assert by_slug.json()['id'] == me['id']


@pytest.mark.asyncio
async def test_public_profile_unknown_returns_404(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=511)
    r = await async_client.get(f'/api/users/{uuid4()}')
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_public_profile_requires_auth(async_client: AsyncClient) -> None:
    r = await async_client.get(f'/api/users/{uuid4()}')
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_list_user_cards_empty(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=512)
    r = await async_client.get(f'/api/users/{me["id"]}/cards')
    assert r.status_code == 200
    data = r.json()
    assert data['items'] == []
    assert data['next_cursor'] is None


@pytest.mark.asyncio
async def test_list_user_cards_unknown_user(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=513)
    r = await async_client.get(f'/api/users/{uuid4()}/cards')
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_create_subscription_and_list_following(async_client: AsyncClient) -> None:
    target = await _login(async_client, telegram_user_id=514)
    await _login(async_client, telegram_user_id=515)

    create = await async_client.post(f'/api/users/{target["id"]}/subscriptions')
    assert create.status_code == 204

    listed = await async_client.get(
        f'/api/users/{target["id"]}/subscriptions',
        params={'type': 'followers'},
    )
    assert listed.status_code == 200
    assert len(listed.json()['items']) == 1
    assert listed.json()['items'][0]['relation_type'] == 'follower'


@pytest.mark.asyncio
async def test_create_subscription_duplicate_returns_409(async_client: AsyncClient) -> None:
    target = await _login(async_client, telegram_user_id=516)
    await _login(async_client, telegram_user_id=517)

    first = await async_client.post(f'/api/users/{target["id"]}/subscriptions')
    assert first.status_code == 204

    second = await async_client.post(f'/api/users/{target["id"]}/subscriptions')
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_create_subscription_to_self_returns_422(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=518)
    r = await async_client.post(f'/api/users/{me["id"]}/subscriptions')
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_delete_subscription(async_client: AsyncClient) -> None:
    target = await _login(async_client, telegram_user_id=519)
    await _login(async_client, telegram_user_id=520)

    create = await async_client.post(f'/api/users/{target["id"]}/subscriptions')
    assert create.status_code == 204

    delete = await async_client.delete(f'/api/users/{target["id"]}/subscriptions')
    assert delete.status_code == 204

    listed = await async_client.get(
        f'/api/users/{target["id"]}/subscriptions',
        params={'type': 'followers'},
    )
    assert listed.status_code == 200
    assert listed.json()['items'] == []


@pytest.mark.asyncio
async def test_list_subscriptions_by_type_and_both(async_client: AsyncClient) -> None:
    u1 = await _login(async_client, telegram_user_id=521)
    u2 = await _login(async_client, telegram_user_id=522)
    u3 = await _login(async_client, telegram_user_id=523)

    # u3 follows u1
    r1 = await async_client.post(f'/api/users/{u1["id"]}/subscriptions')
    assert r1.status_code == 204

    # u3 follows u2
    r2 = await async_client.post(f'/api/users/{u2["id"]}/subscriptions')
    assert r2.status_code == 204

    # u1 follows u3 (mutual relation between u1 and u3)
    await _login(async_client, telegram_user_id=521)
    r3 = await async_client.post(f'/api/users/{u3["id"]}/subscriptions')
    assert r3.status_code == 204

    await _login(async_client, telegram_user_id=522)

    followers = await async_client.get(
        f'/api/users/{u1["id"]}/subscriptions',
        params={'type': 'followers'},
    )
    assert followers.status_code == 200
    assert {item['id'] for item in followers.json()['items']} == {u3['id']}
    assert {item['relation_type'] for item in followers.json()['items']} == {'follower'}

    following = await async_client.get(
        f'/api/users/{u3["id"]}/subscriptions',
        params={'type': 'following'},
    )
    assert following.status_code == 200
    assert {item['id'] for item in following.json()['items']} == {u1['id'], u2['id']}
    assert {item['relation_type'] for item in following.json()['items']} == {'following'}

    both = await async_client.get(
        f'/api/users/{u3["id"]}/subscriptions',
        params={'type': 'both'},
    )
    assert both.status_code == 200
    both_items = both.json()['items']
    assert {(item['id'], item['relation_type']) for item in both_items} == {
        (u1['id'], 'follower'),
        (u1['id'], 'following'),
        (u2['id'], 'following'),
    }


@pytest.mark.asyncio
async def test_subscriptions_unknown_user_returns_404(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=524)
    r = await async_client.get(
        f'/api/users/{uuid4()}/subscriptions',
        params={'type': 'both'},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_subscriptions_require_auth(async_client: AsyncClient) -> None:
    r = await async_client.get(
        f'/api/users/{uuid4()}/subscriptions',
        params={'type': 'followers'},
    )
    assert r.status_code == 401
