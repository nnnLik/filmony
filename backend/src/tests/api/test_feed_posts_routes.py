from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID

import orjson
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from celery_app import app as celery_app_instance
from conf import settings
from core.database import get_session_factory
from models.card_comment import CardComment
from models.catalog_item import CatalogProvider
from models.film import Film
from models.reaction_type import ReactionType
from models.user import User
from models.user_card import UserCard
from tests.auth.telegram_init_data import build_init_data
from tests.support.user_card_category import ensure_default_category


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
        cat_id = await ensure_default_category(session, user_id)
        card = UserCard(
            user_id=user_id,
            film_id=film.id,
            category_id=cat_id,
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
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
        cat_id = await ensure_default_category(session, user_id)
        card = UserCard(
            user_id=user_id,
            film_id=film.id,
            category_id=cat_id,
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
            rating=7.0,
            company='alone',
            mood_before='laugh',
            mood_after='laughed',
        )
        session.add(card)
        await session.flush()
        comment = CardComment(
            card_id=card.id,
            user_id=user_id,
            parent_comment_id=None,
            text='Мой коммент для поста',
        )
        session.add(comment)
        await session.commit()
        await session.refresh(comment)
        comm_id = comment.id
        card_id = card.id

    r_empty = await async_client.post('/api/feed-posts', json={'source_comment_id': comm_id})
    assert r_empty.status_code == 400

    r = await async_client.post(
        '/api/feed-posts',
        json={'source_comment_id': comm_id, 'body': 'Текст поста, не комментарий'},
    )
    assert r.status_code == 200
    data = r.json()
    assert data['body'] == 'Текст поста, не комментарий'
    assert data['referenced_movie_card_id'] == card_id
    assert data['source_comment_id'] == comm_id

    got = await async_client.get(f'/api/feed-posts/{data["id"]}')
    assert got.status_code == 200
    quote = got.json().get('source_comment')
    assert quote is not None
    assert quote['text'] == 'Мой коммент для поста'
    assert quote['author']['id'] == str(user_id)


@pytest.mark.asyncio
async def test_feed_post_from_own_comment_empty_body_ok_with_comment_image(
    async_client: AsyncClient,
) -> None:
    await _login(async_client, telegram_user_id=713)
    film = await _create_film(kinopoisk_id=200098)
    user_id = await _get_user_id(713)
    session_factory = get_session_factory()
    async with session_factory() as session:
        cat_id = await ensure_default_category(session, user_id)
        card = UserCard(
            user_id=user_id,
            film_id=film.id,
            category_id=cat_id,
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
            rating=8.0,
            company='alone',
            mood_before='laugh',
            mood_after='laughed',
        )
        session.add(card)
        await session.flush()
        comment = CardComment(
            card_id=card.id,
            user_id=user_id,
            parent_comment_id=None,
            text='',
            image_url='https://example.com/comment_only.png',
        )
        session.add(comment)
        await session.commit()
        await session.refresh(comment)
        comm_id = comment.id

    r = await async_client.post('/api/feed-posts', json={'source_comment_id': comm_id})
    assert r.status_code == 200
    data = r.json()
    assert data['body'] == ''
    assert data['image_url'] == 'https://example.com/comment_only.png'
    assert data['source_comment_id'] == comm_id


@pytest.mark.asyncio
async def test_feed_post_from_comment_forbidden_other_author(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=707)
    film = await _create_film(kinopoisk_id=200004)
    uid707 = await _get_user_id(707)
    await _login(async_client, telegram_user_id=708)
    session_factory = get_session_factory()
    async with session_factory() as session:
        cat_id = await ensure_default_category(session, uid707)
        card = UserCard(
            user_id=uid707,
            film_id=film.id,
            category_id=cat_id,
            provider=CatalogProvider.kinopoisk,
            external_id=str(film.kinopoisk_id),
            rating=6.0,
            company='alone',
            mood_before='relax',
            mood_after='enjoyed',
        )
        session.add(card)
        await session.flush()
        comment = CardComment(
            card_id=card.id,
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
        cat_id = await ensure_default_category(session, user_id)
        c1 = UserCard(
            user_id=user_id,
            film_id=film_a.id,
            category_id=cat_id,
            provider=CatalogProvider.kinopoisk,
            external_id=str(film_a.kinopoisk_id),
            rating=5.0,
            company='alone',
            mood_before='relax',
            mood_after='tense',
        )
        c2 = UserCard(
            user_id=user_id,
            film_id=film_b.id,
            category_id=cat_id,
            provider=CatalogProvider.kinopoisk,
            external_id=str(film_b.kinopoisk_id),
            rating=6.0,
            company='alone',
            mood_before='thrill',
            mood_after='tense',
        )
        session.add_all([c1, c2])
        await session.flush()
        comment = CardComment(
            card_id=c1.id,
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
    data = r.json()
    assert data['body'] == 'find me'
    assert data['kind'] == 'feed_post'
    assert 'author' in data
    assert 'reactions' in data and 'counts' in data['reactions']
    assert data['comments_count'] == 0
    assert data['comments_preview'] == []

    r404 = await async_client.get('/api/feed-posts/999999')
    assert r404.status_code == 404


@pytest.mark.asyncio
async def test_feed_post_comments_create_and_list(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=740)
    create = await async_client.post('/api/feed-posts', json={'body': 'post root'})
    assert create.status_code == 200
    pid = int(create.json()['id'])

    r_com = await async_client.post(
        f'/api/feed-posts/{pid}/comments',
        json={'text': ' first reply '},
    )
    assert r_com.status_code == 200
    assert r_com.json()['text'] == 'first reply'
    assert r_com.json()['feed_post_id'] == pid

    lst = await async_client.get(f'/api/feed-posts/{pid}/comments')
    assert lst.status_code == 200
    bodies = [it['text'] for it in lst.json()['items']]
    assert 'first reply' in bodies


@pytest.mark.asyncio
async def test_feed_post_comment_reply_and_reaction(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=741)
    create = await async_client.post('/api/feed-posts', json={'body': 'thr'})
    pid = int(create.json()['id'])
    root = await async_client.post(
        f'/api/feed-posts/{pid}/comments',
        json={'text': 'root c'},
    )
    assert root.status_code == 200
    root_id = int(root.json()['id'])

    rep = await async_client.post(
        f'/api/feed-posts/{pid}/comments',
        json={'text': 'nested', 'parent_comment_id': root_id},
    )
    assert rep.status_code == 200
    assert rep.json()['parent_comment_id'] == root_id

    replies = await async_client.get(f'/api/feed-posts/{pid}/comments/{root_id}/replies')
    assert replies.status_code == 200
    assert len(replies.json()['items']) >= 1

    session_factory = get_session_factory()
    async with session_factory() as session:
        rt = ReactionType(
            image_url='https://example.com/fpc_rx.png',
            category_slug='feed_post_test',
            asset_key='reactions/feed_post_test/x.png',
        )
        session.add(rt)
        await session.commit()
        await session.refresh(rt)
        tid = int(rt.id)

    rx = await async_client.post(
        '/api/reactions',
        json={
            'target_kind': 'feed_post_comment',
            'target_id': root_id,
            'reaction_type_id': tid,
        },
    )
    assert rx.status_code == 200
    assert rx.json()['target_kind'] == 'feed_post_comment'


@pytest.mark.asyncio
async def test_feed_post_reaction_on_post(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=742)
    create = await async_client.post('/api/feed-posts', json={'body': 'post for rx'})
    pid = int(create.json()['id'])

    session_factory = get_session_factory()
    async with session_factory() as session:
        rt = ReactionType(
            image_url='https://example.com/fp_rx.png',
            category_slug='feed_post_rx2',
            asset_key='reactions/feed_post_rx2/x.png',
        )
        session.add(rt)
        await session.commit()
        await session.refresh(rt)
        tid = int(rt.id)

    rx = await async_client.post(
        '/api/reactions',
        json={
            'target_kind': 'feed_post',
            'target_id': pid,
            'reaction_type_id': tid,
        },
    )
    assert rx.status_code == 200
    assert rx.json()['target_kind'] == 'feed_post'
    assert rx.json()['target_id'] == pid
    assert len(rx.json()['reactions']['counts']) >= 1

    detail = await async_client.get(f'/api/feed-posts/{pid}')
    assert detail.status_code == 200
    mine = detail.json()['reactions'].get('my_reaction_type_ids') or []
    assert tid in mine


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
    listed = orjson.loads(kwargs['recipient_user_ids_json'])
    assert listed == [recipient_id]


@pytest.mark.asyncio
async def test_feed_post_comment_mention_queues_celery(
    monkeypatch: pytest.MonkeyPatch, async_client: AsyncClient
) -> None:
    mock_delay = MagicMock()
    monkeypatch.setattr(
        celery_app_instance.tasks['tasks.telegram_engagement.notify_feed_post_comment_mentions'],
        'delay',
        mock_delay,
    )

    author = await _login(async_client, telegram_user_id=736)
    target = await _login(async_client, telegram_user_id=737)
    slug_target = await _profile_slug_for_tg(737)
    await _login(async_client, telegram_user_id=736)
    await async_client.post(f'/api/users/{target["id"]}/subscriptions')

    post = await async_client.post('/api/feed-posts', json={'body': 'post for comment mention'})
    assert post.status_code == 200
    pid = int(post.json()['id'])

    token = f'⟦@{slug_target}⟧'
    com = await async_client.post(
        f'/api/feed-posts/{pid}/comments',
        json={'text': f'Привет {token}'},
    )
    assert com.status_code == 200
    comment_id = int(com.json()['id'])

    recipient_id = str(await _get_user_id(737))
    mock_delay.assert_called_once()
    kwargs = mock_delay.call_args.kwargs
    assert kwargs['actor_user_id'] == author['id']
    assert kwargs['feed_post_id'] == pid
    assert kwargs['comment_id'] == comment_id
    listed = orjson.loads(kwargs['recipient_user_ids_json'])
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


@pytest.mark.asyncio
async def test_feed_post_create_queues_follower_publish_notify(
    monkeypatch: pytest.MonkeyPatch, async_client: AsyncClient
) -> None:
    mock_delay = MagicMock()
    task = celery_app_instance.tasks['tasks.telegram_engagement.notify_followers_new_feed_post']
    monkeypatch.setattr(task, 'delay', mock_delay)

    author = await _login(async_client, telegram_user_id=764)
    await _login(async_client, telegram_user_id=765)
    await async_client.post(f'/api/users/{author["id"]}/subscriptions')

    await _login(async_client, telegram_user_id=764)
    r = await async_client.post('/api/feed-posts', json={'body': 'hello followers'})
    assert r.status_code == 200
    data = r.json()

    mock_delay.assert_called_once()
    kwargs = mock_delay.call_args.kwargs
    assert kwargs['actor_user_id'] == author['id']
    assert kwargs['feed_post_id'] == data['id']
    uid765 = str(await _get_user_id(765))
    listed = orjson.loads(kwargs['recipient_user_ids_json'])
    assert listed == [uid765]


@pytest.mark.asyncio
async def test_feed_post_follower_notify_excludes_mention_recipients(
    monkeypatch: pytest.MonkeyPatch, async_client: AsyncClient
) -> None:
    mock_mention = MagicMock()
    mock_follower = MagicMock()
    monkeypatch.setattr(
        celery_app_instance.tasks['tasks.telegram_engagement.notify_feed_post_mentions'],
        'delay',
        mock_mention,
    )
    monkeypatch.setattr(
        celery_app_instance.tasks['tasks.telegram_engagement.notify_followers_new_feed_post'],
        'delay',
        mock_follower,
    )

    author = await _login(async_client, telegram_user_id=766)
    mentioned_follower = await _login(async_client, telegram_user_id=767)
    slug_m = await _profile_slug_for_tg(767)
    other_follower = await _login(async_client, telegram_user_id=768)

    await _login(async_client, telegram_user_id=767)
    await async_client.post(f'/api/users/{author["id"]}/subscriptions')
    await _login(async_client, telegram_user_id=768)
    await async_client.post(f'/api/users/{author["id"]}/subscriptions')

    await _login(async_client, telegram_user_id=766)
    await async_client.post(f'/api/users/{mentioned_follower["id"]}/subscriptions')

    await _login(async_client, telegram_user_id=766)
    token = f'⟦@{slug_m}⟧'
    r = await async_client.post('/api/feed-posts', json={'body': f'Hey {token}'})
    assert r.status_code == 200

    mock_mention.assert_called_once()
    mock_follower.assert_called_once()
    mention_ids = orjson.loads(mock_mention.call_args.kwargs['recipient_user_ids_json'])
    assert mention_ids == [str(mentioned_follower['id'])]
    follower_ids = orjson.loads(mock_follower.call_args.kwargs['recipient_user_ids_json'])
    assert follower_ids == [str(other_follower['id'])]


@pytest.mark.asyncio
async def test_feed_post_only_followers_mentioned_skips_follower_broadcast(
    monkeypatch: pytest.MonkeyPatch, async_client: AsyncClient
) -> None:
    mock_follower = MagicMock()
    monkeypatch.setattr(
        celery_app_instance.tasks['tasks.telegram_engagement.notify_followers_new_feed_post'],
        'delay',
        mock_follower,
    )

    author = await _login(async_client, telegram_user_id=778)
    only_follower = await _login(async_client, telegram_user_id=779)
    slug_only = await _profile_slug_for_tg(779)
    await _login(async_client, telegram_user_id=779)
    await async_client.post(f'/api/users/{author["id"]}/subscriptions')

    await _login(async_client, telegram_user_id=778)
    await async_client.post(f'/api/users/{only_follower["id"]}/subscriptions')

    await _login(async_client, telegram_user_id=778)
    token = f'⟦@{slug_only}⟧'
    r = await async_client.post('/api/feed-posts', json={'body': f'Solo hey {token}'})
    assert r.status_code == 200
    mock_follower.assert_not_called()


@pytest.mark.asyncio
async def test_feed_post_create_no_followers_skips_follower_notify(
    monkeypatch: pytest.MonkeyPatch, async_client: AsyncClient
) -> None:
    mock_delay = MagicMock()
    task = celery_app_instance.tasks['tasks.telegram_engagement.notify_followers_new_feed_post']
    monkeypatch.setattr(task, 'delay', mock_delay)

    await _login(async_client, telegram_user_id=769)
    r = await async_client.post('/api/feed-posts', json={'body': 'solo'})
    assert r.status_code == 200
    mock_delay.assert_not_called()


@pytest.mark.asyncio
async def test_feed_post_only_mention_follower_skips_follower_broadcast(
    monkeypatch: pytest.MonkeyPatch, async_client: AsyncClient
) -> None:
    mock_mention = MagicMock()
    mock_follower = MagicMock()
    monkeypatch.setattr(
        celery_app_instance.tasks['tasks.telegram_engagement.notify_feed_post_mentions'],
        'delay',
        mock_mention,
    )
    monkeypatch.setattr(
        celery_app_instance.tasks['tasks.telegram_engagement.notify_followers_new_feed_post'],
        'delay',
        mock_follower,
    )

    author = await _login(async_client, telegram_user_id=771)
    user772 = await _login(async_client, telegram_user_id=772)
    slug_t = await _profile_slug_for_tg(772)
    await _login(async_client, telegram_user_id=772)
    await async_client.post(f'/api/users/{author["id"]}/subscriptions')
    await _login(async_client, telegram_user_id=771)
    # Mention tokens require the author to follow the mentioned user (see validate_inline_mention_tokens).
    await async_client.post(f'/api/users/{user772["id"]}/subscriptions')
    token = f'⟦@{slug_t}⟧'
    r = await async_client.post('/api/feed-posts', json={'body': f'Only you {token}'})
    assert r.status_code == 200

    mock_mention.assert_called_once()
    mock_follower.assert_not_called()


@pytest.mark.asyncio
async def test_feed_post_comment_update_and_delete(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=8801)
    create = await async_client.post('/api/feed-posts', json={'body': 'post for edit'})
    assert create.status_code == 200
    pid = int(create.json()['id'])

    com = await async_client.post(
        f'/api/feed-posts/{pid}/comments',
        json={'text': 'original text'},
    )
    assert com.status_code == 200
    cid = int(com.json()['id'])

    updated = await async_client.patch(
        f'/api/feed-posts/{pid}/comments/{cid}',
        json={'text': '  revised text  '},
    )
    assert updated.status_code == 200
    assert updated.json()['text'] == 'revised text'

    await _login(async_client, telegram_user_id=8802)
    forbidden = await async_client.patch(
        f'/api/feed-posts/{pid}/comments/{cid}',
        json={'text': 'hack'},
    )
    assert forbidden.status_code == 403

    await _login(async_client, telegram_user_id=8801)
    deleted = await async_client.delete(f'/api/feed-posts/{pid}/comments/{cid}')
    assert deleted.status_code == 204

    lst = await async_client.get(f'/api/feed-posts/{pid}/comments')
    assert lst.status_code == 200
    assert all(it['id'] != cid for it in lst.json()['items'])

    await _login(async_client, telegram_user_id=8802)
    del_forbidden = await async_client.delete(f'/api/feed-posts/{pid}/comments/{cid}')
    assert del_forbidden.status_code == 404


@pytest.mark.asyncio
async def test_feed_post_comment_update_wrong_post(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=8803)
    p1 = await async_client.post('/api/feed-posts', json={'body': 'p1'})
    p2 = await async_client.post('/api/feed-posts', json={'body': 'p2'})
    pid1 = int(p1.json()['id'])
    pid2 = int(p2.json()['id'])
    com = await async_client.post(
        f'/api/feed-posts/{pid1}/comments',
        json={'text': 'on p1'},
    )
    cid = int(com.json()['id'])

    mismatch = await async_client.patch(
        f'/api/feed-posts/{pid2}/comments/{cid}',
        json={'text': 'wrong post'},
    )
    assert mismatch.status_code == 404
