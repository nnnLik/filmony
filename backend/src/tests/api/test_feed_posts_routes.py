from __future__ import annotations

import json
from unittest.mock import MagicMock
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from celery_app import app as celery_app_instance
from conf import settings
from core.database import get_session_factory
from models.film import Film
from models.movie_card import MovieCard
from models.movie_card_comment import MovieCardComment
from models.user import User
from tests.auth.telegram_init_data import build_init_data


async def _login(async_client: AsyncClient, telegram_user_id: int) -> dict[str, object]:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    r = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert r.status_code == 200
    return r.json()


async def _create_film(*, kinopoisk_id: int = 200001) -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title='Test Film',
            year=2020,
            poster_url='https://example.com/p.jpg',
            genres=['драма'],
        )
        session.add(film)
        await session.commit()
        await session.refresh(film)
        return film


async def _get_user_id(telegram_user_id: int) -> object:
    session_factory = get_session_factory()
    async with session_factory() as session:
        u = (
            await session.execute(select(User).where(User.telegram_user_id == telegram_user_id))
        ).scalar_one()
        return u.id


async def _profile_slug_for_tg(telegram_user_id: int) -> str:
    session_factory = get_session_factory()
    async with session_factory() as session:
        slug = (
            await session.execute(
                select(User.profile_slug).where(User.telegram_user_id == telegram_user_id)
            )
        ).scalar_one()
        return str(slug)


@pytest.mark.asyncio
async def test_feed_post_create_requires_auth(async_client: AsyncClient) -> None:
    r = await async_client.post('/api/feed-posts', json={'body': 'hello'})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_feed_post_get_requires_auth(async_client: AsyncClient) -> None:
    r = await async_client.get('/api/feed-posts/1')
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_feed_post_create_text_only(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=701)
    r = await async_client.post('/api/feed-posts', json={'body': '  Привет с ленты  '})
    assert r.status_code == 200
    data = r.json()
    assert data['body'] == 'Привет с ленты'
    assert data['image_url'] is None
    assert data['referenced_movie_card_id'] is None
    assert data['source_comment_id'] is None
    assert 'id' in data


@pytest.mark.asyncio
async def test_user_feed_posts_profile_list(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=705)
    r = await async_client.post('/api/feed-posts', json={'body': 'profile_tab_post_body'})
    assert r.status_code == 200
    uid = str(await _get_user_id(705))
    await _login(async_client, telegram_user_id=705)
    lst = await async_client.get(f'/api/users/{uid}/feed-posts?limit=10')
    assert lst.status_code == 200
    data = lst.json()
    assert 'items' in data and 'next_cursor' in data
    bodies = [it['body'] for it in data['items'] if it.get('kind') == 'feed_post']
    assert 'profile_tab_post_body' in bodies


@pytest.mark.asyncio
async def test_feed_post_from_author_appears_in_movie_card_feed(async_client: AsyncClient) -> None:
    """Собственные текстовые посты не должны отфильтровываться вместе со своими карточками."""
    me = await _login(async_client, telegram_user_id=704)
    my_id = UUID(str(me['id']))
    r = await async_client.post('/api/feed-posts', json={'body': 'only_me_feed_post_marker'})
    assert r.status_code == 200
    post_id = int(r.json()['id'])

    await _login(async_client, telegram_user_id=704)
    feed = await async_client.get('/api/cards/feed?limit=50')
    assert feed.status_code == 200
    items = feed.json()['items']
    hits = [
        it
        for it in items
        if it.get('kind') == 'feed_post'
        and it.get('id') == post_id
        and it.get('user_id') == str(my_id)
        and it.get('body') == 'only_me_feed_post_marker'
    ]
    assert len(hits) == 1


@pytest.mark.asyncio
async def test_feed_post_create_image_only(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=702)
    r = await async_client.post(
        '/api/feed-posts',
        json={'body': '', 'image_url': 'https://cdn.example.com/x.png'},
    )
    assert r.status_code == 200
    data = r.json()
    assert data['body'] == ''
    assert data['image_url'] == 'https://cdn.example.com/x.png'


@pytest.mark.asyncio
async def test_feed_post_create_empty_rejected(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=703)
    r = await async_client.post('/api/feed-posts', json={'body': '   '})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_feed_post_create_with_referenced_card(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=704)
    film = await _create_film(kinopoisk_id=200002)
    user_id = await _get_user_id(704)
    session_factory = get_session_factory()
    async with session_factory() as session:
        card = MovieCard(
            user_id=user_id,
            film_id=film.id,
            rating=8.0,
            company='alone',
            mood_before='relax',
            mood_after='enjoyed',
        )
        session.add(card)
        await session.commit()
        await session.refresh(card)
        cid = card.id

    r = await async_client.post(
        '/api/feed-posts',
        json={'body': 'Классный фильм', 'referenced_movie_card_id': cid},
    )
    assert r.status_code == 200
    assert r.json()['referenced_movie_card_id'] == cid


@pytest.mark.asyncio
async def test_feed_post_create_referenced_card_not_found(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=705)
    r = await async_client.post(
        '/api/feed-posts',
        json={'body': 'x', 'referenced_movie_card_id': 999999},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_feed_post_from_own_comment(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=706)
    film = await _create_film(kinopoisk_id=200003)
    user_id = await _get_user_id(706)
    session_factory = get_session_factory()
    async with session_factory() as session:
        card = MovieCard(
            user_id=user_id,
            film_id=film.id,
            rating=7.0,
            company='alone',
            mood_before='laugh',
            mood_after='laughed',
        )
        session.add(card)
        await session.flush()
        comment = MovieCardComment(
            movie_card_id=card.id,
            user_id=user_id,
            parent_comment_id=None,
            text='Мой коммент для поста',
        )
        session.add(comment)
        await session.commit()
        await session.refresh(comment)
        comm_id = comment.id
        card_id = card.id

    r = await async_client.post('/api/feed-posts', json={'source_comment_id': comm_id})
    assert r.status_code == 200
    data = r.json()
    assert data['body'] == 'Мой коммент для поста'
    assert data['referenced_movie_card_id'] == card_id
    assert data['source_comment_id'] == comm_id


@pytest.mark.asyncio
async def test_feed_post_from_comment_forbidden_other_author(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=707)
    film = await _create_film(kinopoisk_id=200004)
    uid707 = await _get_user_id(707)
    await _login(async_client, telegram_user_id=708)
    session_factory = get_session_factory()
    async with session_factory() as session:
        card = MovieCard(
            user_id=uid707,
            film_id=film.id,
            rating=6.0,
            company='alone',
            mood_before='relax',
            mood_after='enjoyed',
        )
        session.add(card)
        await session.flush()
        comment = MovieCardComment(
            movie_card_id=card.id,
            user_id=uid707,
            parent_comment_id=None,
            text='Чужой',
        )
        session.add(comment)
        await session.commit()
        await session.refresh(comment)
        comm_id = comment.id

    r = await async_client.post('/api/feed-posts', json={'source_comment_id': comm_id})
    assert r.status_code == 403

    await _login(async_client, telegram_user_id=708)
    r2 = await async_client.post(
        '/api/feed-posts',
        json={'source_comment_id': comm_id, 'body': 'Пытаюсь подставить чужой'},
    )
    assert r2.status_code == 403


@pytest.mark.asyncio
async def test_feed_post_from_comment_mismatched_card_id(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=709)
    film_a = await _create_film(kinopoisk_id=200005)
    film_b = await _create_film(kinopoisk_id=200006)
    user_id = await _get_user_id(709)
    session_factory = get_session_factory()
    async with session_factory() as session:
        c1 = MovieCard(
            user_id=user_id,
            film_id=film_a.id,
            rating=5.0,
            company='alone',
            mood_before='relax',
            mood_after='tense',
        )
        c2 = MovieCard(
            user_id=user_id,
            film_id=film_b.id,
            rating=6.0,
            company='alone',
            mood_before='thrill',
            mood_after='tense',
        )
        session.add_all([c1, c2])
        await session.flush()
        comment = MovieCardComment(
            movie_card_id=c1.id,
            user_id=user_id,
            parent_comment_id=None,
            text='x',
        )
        session.add(comment)
        await session.commit()
        await session.refresh(comment)

    r = await async_client.post(
        '/api/feed-posts',
        json={'source_comment_id': comment.id, 'referenced_movie_card_id': c2.id},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_feed_post_get_by_id(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=710)
    create = await async_client.post('/api/feed-posts', json={'body': 'find me'})
    pid = create.json()['id']

    await _login(async_client, telegram_user_id=711)
    r = await async_client.get(f'/api/feed-posts/{pid}')
    assert r.status_code == 200
    assert r.json()['body'] == 'find me'

    r404 = await async_client.get('/api/feed-posts/999999')
    assert r404.status_code == 404


@pytest.mark.asyncio
async def test_feed_post_upload_requires_auth(async_client: AsyncClient) -> None:
    r = await async_client.post(
        '/api/feed-posts/upload',
        files={'file': ('x.jpg', b'hello', 'image/jpeg')},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_feed_post_upload_success(monkeypatch, async_client: AsyncClient) -> None:
    from api.feed_posts import routes as feed_posts_routes_module

    class FakeUpload:
        @classmethod
        def build(cls):
            return cls()

        async def execute(self, **_kwargs):
            return '/api/feed-posts/media/user_media/feed_posts/x/y.jpg'

    monkeypatch.setattr(feed_posts_routes_module, 'UploadFeedPostImageService', FakeUpload)
    await _login(async_client, telegram_user_id=720)
    r = await async_client.post(
        '/api/feed-posts/upload',
        files={'file': ('x.jpg', b'hello', 'image/jpeg')},
    )
    assert r.status_code == 200
    assert r.json()['url'] == '/api/feed-posts/media/user_media/feed_posts/x/y.jpg'


@pytest.mark.asyncio
async def test_feed_post_upload_rejects_bad_type(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=721)
    r = await async_client.post(
        '/api/feed-posts/upload',
        files={'file': ('x.bin', b'hello', 'application/octet-stream')},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_feed_post_media_unsafe_key(async_client: AsyncClient) -> None:
    r = await async_client.get('/api/feed-posts/media/other-prefix/x.jpg')
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_feed_post_media_not_configured(monkeypatch, async_client: AsyncClient) -> None:
    from conf import settings

    monkeypatch.setattr(settings.reaction_media, 'rustfs_internal_base_url', '')
    r = await async_client.get('/api/feed-posts/media/user_media/feed_posts/u/f.jpg')
    assert r.status_code == 503


@pytest.mark.asyncio
async def test_feed_post_mention_valid_queues_celery(
    monkeypatch: pytest.MonkeyPatch, async_client: AsyncClient
) -> None:
    mock_delay = MagicMock()
    mention_task = celery_app_instance.tasks['tasks.telegram_engagement.notify_feed_post_mentions']
    monkeypatch.setattr(mention_task, 'delay', mock_delay)

    author = await _login(async_client, telegram_user_id=730)
    target = await _login(async_client, telegram_user_id=731)
    slug_target = await _profile_slug_for_tg(731)
    await _login(async_client, telegram_user_id=730)
    await async_client.post(f'/api/users/{target["id"]}/subscriptions')

    token = f'⟦@{slug_target}⟧'
    r = await async_client.post('/api/feed-posts', json={'body': f'Привет {token}'})
    assert r.status_code == 200
    data = r.json()
    assert 'Привет' in data['body']
    assert '⟦@' in data['body'] and slug_target.lower() in data['body'].lower()

    recipient_id = str(await _get_user_id(731))
    mock_delay.assert_called_once()
    kwargs = mock_delay.call_args.kwargs
    assert kwargs['actor_user_id'] == author['id']
    assert kwargs['feed_post_id'] == data['id']
    listed = json.loads(kwargs['recipient_user_ids_json'])
    assert listed == [recipient_id]


@pytest.mark.asyncio
async def test_feed_post_mention_unknown_slug(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=732)
    r = await async_client.post(
        '/api/feed-posts',
        json={'body': 'hi ⟦@this_slug_does_not_exist_zz99⟧'},
    )
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_feed_post_mention_not_following(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=733)
    await _login(async_client, telegram_user_id=734)
    slug_other = await _profile_slug_for_tg(734)
    await _login(async_client, telegram_user_id=733)  # author without subscription to 734
    r = await async_client.post('/api/feed-posts', json={'body': f'hi ⟦@{slug_other}⟧'})
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_feed_post_mention_self_forbidden(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=735)
    slug = await _profile_slug_for_tg(735)
    r = await async_client.post('/api/feed-posts', json={'body': f'⟦@{slug}⟧'})
    assert r.status_code == 400
