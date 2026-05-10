import asyncio
from uuid import UUID, uuid4

import pytest
from httpx import AsyncClient

from conf import settings
from core.database import get_session_factory
from models.film import Film
from models.movie_card import MovieCard
from models.movie_card_tag import MovieCardTag
from tests.auth.telegram_init_data import build_init_data


async def _login(async_client: AsyncClient, telegram_user_id: int) -> dict[str, object]:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    r = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert r.status_code == 200
    return r.json()


async def _seed_movie_card(
    *,
    user_id: UUID,
    kinopoisk_id: int,
    title: str,
    year: int | None,
    rating: float,
    company: str,
    mood_before: str = 'relax',
    mood_after: str,
    tags: list[str],
) -> int:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title=title,
            year=year,
            poster_url='https://example.com/poster.jpg',
            genres=[],
        )
        session.add(film)
        await session.flush()
        card = MovieCard(
            user_id=user_id,
            film_id=film.id,
            rating=rating,
            company=company,
            mood_before=mood_before,
            mood_after=mood_after,
        )
        session.add(card)
        await session.flush()
        for tag in tags:
            session.add(MovieCardTag(movie_card_id=card.id, tag=tag))
        await session.commit()
        return card.id


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
    assert body['favorites_count'] == 0
    assert body['watchlist_count'] == 0
    assert body['friends_count'] == 0
    assert body['followers_count'] == 0
    assert body['following_count'] == 0


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
async def test_patch_my_profile_rejects_unknown_field(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=508)
    r = await async_client.patch('/api/me/profile', json={'hacker_field': 'x'})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_public_profile_by_id(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=509)
    await _login(async_client, telegram_user_id=510)

    by_id = await async_client.get(f'/api/users/{me["id"]}')
    assert by_id.status_code == 200
    assert by_id.json()['profile_slug']
    assert 'telegram_user_id' not in by_id.json()


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
    target_before = await async_client.get('/api/me/profile')
    assert target_before.json()['followers_count'] == 0
    assert target_before.json()['following_count'] == 0

    follower = await _login(async_client, telegram_user_id=515)

    create = await async_client.post(f'/api/users/{target["id"]}/subscriptions')
    assert create.status_code == 204

    me_profile = await async_client.get('/api/me/profile')
    assert me_profile.status_code == 200
    assert me_profile.json()['following_count'] == 1
    assert me_profile.json()['followers_count'] == 0

    await _login(async_client, telegram_user_id=514)
    target_after = await async_client.get('/api/me/profile')
    assert target_after.json()['followers_count'] == 1
    assert target_after.json()['following_count'] == 0

    pub = await async_client.get(f'/api/users/{target["id"]}')
    assert pub.status_code == 200
    assert pub.json()['followers_count'] == 1
    assert pub.json()['following_count'] == 0

    await _login(async_client, telegram_user_id=515)
    pub_follower = await async_client.get(f'/api/users/{follower["id"]}')
    assert pub_follower.json()['following_count'] == 1
    assert pub_follower.json()['followers_count'] == 0

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


@pytest.mark.asyncio
async def test_user_stats_requires_auth(async_client: AsyncClient) -> None:
    r = await async_client.get(f'/api/users/{uuid4()}/stats')
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_user_stats_unknown_user_returns_404(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=525)
    r = await async_client.get(f'/api/users/{uuid4()}/stats')
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_user_stats_aggregates(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=526)
    user_id = UUID(str(me['id']))
    await _seed_movie_card(
        user_id=user_id,
        kinopoisk_id=200001,
        title='Фильм A',
        year=2024,
        rating=10.0,
        company='alone',
        mood_after='cried',
        tags=['Шедевр', 'Ноланомания'],
    )
    await _seed_movie_card(
        user_id=user_id,
        kinopoisk_id=200002,
        title='Фильм B',
        year=2023,
        rating=9.0,
        company='friends',
        mood_after='laughed',
        tags=['Шедевр'],
    )
    await _seed_movie_card(
        user_id=user_id,
        kinopoisk_id=200003,
        title='Фильм C',
        year=2023,
        rating=9.0,
        company='friends',
        mood_after='laughed',
        tags=['Эпик'],
    )
    await _seed_movie_card(
        user_id=user_id,
        kinopoisk_id=200004,
        title='Фильм D',
        year=2021,
        rating=7.0,
        company='partner',
        mood_after='enjoyed',
        tags=['Яркий'],
    )
    await _seed_movie_card(
        user_id=user_id,
        kinopoisk_id=200005,
        title='Фильм E',
        year=2020,
        rating=7.0,
        company='partner',
        mood_after='wasted_time',
        tags=['Фемповестка'],
    )
    await _seed_movie_card(
        user_id=user_id,
        kinopoisk_id=200006,
        title='Фильм F',
        year=2010,
        rating=1.0,
        company='alone',
        mood_after='cried',
        tags=['Визуал'],
    )

    r = await async_client.get(f'/api/users/{user_id}/stats')
    assert r.status_code == 200
    body = r.json()

    assert body['total_movies'] == 6
    assert body['average_rating'] == 7.2

    ratings = {item['rating']: item['count'] for item in body['rating_distribution']}
    assert ratings[10] == 1
    assert ratings[9] == 2
    assert ratings[7] == 2
    assert ratings[1] == 1

    years = {item['year']: item['count'] for item in body['year_distribution']}
    assert years[2024] == 1
    assert years[2023] == 2
    assert years[2021] == 1
    assert years[2020] == 1
    assert years[2010] == 1

    tags = {item['tag']: item['count'] for item in body['popular_tags']}
    assert tags['Шедевр'] == 2
    assert tags['Ноланомания'] == 1
    assert tags['Эпик'] == 1
    assert tags['Яркий'] == 1
    assert tags['Фемповестка'] == 1

    by_company = {item['value']: item['count'] for item in body['watch_with_distribution']}
    assert by_company['alone'] == 2
    assert by_company['friends'] == 2
    assert by_company['partner'] == 2

    by_mood = {item['value']: item['count'] for item in body['mood_after_distribution']}
    assert by_mood['cried'] == 2
    assert by_mood['laughed'] == 2
    assert by_mood['enjoyed'] == 1
    assert by_mood['wasted_time'] == 1

    assert [item['film_title'] for item in body['top_movies']] == [
        'Фильм A',
        'Фильм B',
        'Фильм C',
        'Фильм D',
        'Фильм E',
    ]
    assert [item['film_title'] for item in body['worst_movies']] == [
        'Фильм F',
        'Фильм D',
        'Фильм E',
        'Фильм B',
        'Фильм C',
    ]


@pytest.mark.asyncio
async def test_favorites_count_and_favorites_only_list(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=9604)
    uid = UUID(str(me['id']))
    card_early = await _seed_movie_card(
        user_id=uid,
        kinopoisk_id=300001,
        title='Early fav',
        year=2020,
        rating=8.0,
        company='alone',
        mood_after='enjoyed',
        tags=[],
    )
    card_late = await _seed_movie_card(
        user_id=uid,
        kinopoisk_id=300002,
        title='Late fav',
        year=2021,
        rating=7.5,
        company='alone',
        mood_after='enjoyed',
        tags=[],
    )

    p1 = await async_client.patch(f'/api/cards/{card_early}', json={'is_favorite': True})
    assert p1.status_code == 200
    await asyncio.sleep(0.02)
    p2 = await async_client.patch(f'/api/cards/{card_late}', json={'is_favorite': True})
    assert p2.status_code == 200

    prof = await async_client.get('/api/me/profile')
    assert prof.status_code == 200
    assert prof.json()['favorites_count'] == 2

    pub = await async_client.get(f'/api/users/{me["id"]}')
    assert pub.status_code == 200
    assert pub.json()['favorites_count'] == 2

    fav = await async_client.get(f'/api/users/{me["id"]}/cards', params={'favorites_only': True})
    assert fav.status_code == 200
    body = fav.json()
    assert [it['id'] for it in body['items']] == [card_late, card_early]
    assert all(it['is_favorite'] for it in body['items'])

    all_cards = await async_client.get(f'/api/users/{me["id"]}/cards')
    assert all_cards.status_code == 200
    fav_ids = {it['id']: it['is_favorite'] for it in all_cards.json()['items']}
    assert fav_ids[card_early] is True
    assert fav_ids[card_late] is True


@pytest.mark.asyncio
async def test_my_movie_card_tags_stats(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=5199)
    uid = UUID(str(me['id']))

    await _seed_movie_card(
        user_id=uid,
        kinopoisk_id=5199001,
        title='A',
        year=2020,
        rating=7.0,
        company='alone',
        mood_after='enjoyed',
        tags=['alpha', 'beta'],
    )
    await _seed_movie_card(
        user_id=uid,
        kinopoisk_id=5199002,
        title='B',
        year=2021,
        rating=8.0,
        company='alone',
        mood_after='enjoyed',
        tags=['alpha', 'gamma'],
    )
    await _seed_movie_card(
        user_id=uid,
        kinopoisk_id=5199003,
        title='C',
        year=2022,
        rating=6.0,
        company='alone',
        mood_after='enjoyed',
        tags=['alpha'],
    )

    r = await async_client.get('/api/me/movie-card-tags')
    assert r.status_code == 200
    items = r.json()['items']
    assert [x['tag'] for x in items] == ['alpha', 'beta', 'gamma']
    assert next(x for x in items if x['tag'] == 'alpha')['use_count'] == 3
    assert next(x for x in items if x['tag'] == 'beta')['use_count'] == 1


@pytest.mark.asyncio
async def test_list_user_movie_card_tags_public(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=5201)
    target = await _login(async_client, telegram_user_id=5202)
    uid = UUID(str(target['id']))

    await _seed_movie_card(
        user_id=uid,
        kinopoisk_id=5202001,
        title='T1',
        year=2020,
        rating=7.0,
        company='alone',
        mood_after='enjoyed',
        tags=['zeta', 'omega'],
    )

    r = await async_client.get(f'/api/users/{uid}/movie-card-tags')
    assert r.status_code == 200
    items = r.json()['items']
    assert {x['tag'] for x in items} == {'zeta', 'omega'}


@pytest.mark.asyncio
async def test_list_user_movie_card_tags_unknown_user(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=5203)
    r = await async_client.get(f'/api/users/{uuid4()}/movie-card-tags')
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_list_user_cards_sort_and_filters(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=5204)
    target = await _login(async_client, telegram_user_id=5205)
    uid = UUID(str(target['id']))

    c_high = await _seed_movie_card(
        user_id=uid,
        kinopoisk_id=5205001,
        title='High',
        year=2024,
        rating=9.0,
        company='friends',
        mood_before='laugh',
        mood_after='laughed',
        tags=['shared', 'cinema'],
    )
    c_mid = await _seed_movie_card(
        user_id=uid,
        kinopoisk_id=5205002,
        title='Mid',
        year=2023,
        rating=5.0,
        company='alone',
        mood_before='relax',
        mood_after='enjoyed',
        tags=['shared'],
    )
    _c_low = await _seed_movie_card(
        user_id=uid,
        kinopoisk_id=5205003,
        title='Low',
        year=1999,
        rating=2.0,
        company='partner',
        mood_before='thrill',
        mood_after='tense',
        tags=['other'],
    )

    r_desc = await async_client.get(
        f'/api/users/{uid}/cards', params={'sort': 'rating_desc', 'limit': 10}
    )
    assert r_desc.status_code == 200
    ids_desc = [x['id'] for x in r_desc.json()['items']]
    assert ids_desc[0] == c_high
    assert c_mid in ids_desc

    r_tag = await async_client.get(
        f'/api/users/{uid}/cards',
        params=[('tag', 'shared'), ('tag', 'cinema')],
    )
    assert r_tag.status_code == 200
    assert [x['id'] for x in r_tag.json()['items']] == [c_high]

    r_year = await async_client.get(
        f'/api/users/{uid}/cards',
        params={'year_min': 2020, 'year_max': 2024, 'sort': 'rating_asc'},
    )
    assert r_year.status_code == 200
    titles = [x['film_title'] for x in r_year.json()['items']]
    assert 'Mid' in titles
    assert 'High' in titles
    assert 'Low' not in titles

    r_mood = await async_client.get(
        f'/api/users/{uid}/cards',
        params={'mood_before': 'laugh', 'mood_after': 'laughed'},
    )
    assert r_mood.status_code == 200
    assert [x['id'] for x in r_mood.json()['items']] == [c_high]

    r_co = await async_client.get(f'/api/users/{uid}/cards', params={'company': 'alone'})
    assert r_co.status_code == 200
    assert {x['id'] for x in r_co.json()['items']} == {c_mid}


@pytest.mark.asyncio
async def test_list_user_cards_invalid_year_range(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=5206)
    r = await async_client.get(
        f'/api/users/{me["id"]}/cards',
        params={'year_min': 2020, 'year_max': 2010},
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_list_user_cards_film_title_substring(async_client: AsyncClient) -> None:
    me = await _login(async_client, telegram_user_id=5210)
    uid = UUID(str(me['id']))
    c_matrix = await _seed_movie_card(
        user_id=uid,
        kinopoisk_id=5210001,
        title='The Matrix Reloaded',
        year=2003,
        rating=8.0,
        company='alone',
        mood_before='relax',
        mood_after='enjoyed',
        tags=[],
    )
    await _seed_movie_card(
        user_id=uid,
        kinopoisk_id=5210002,
        title='Something Else',
        year=2001,
        rating=7.0,
        company='alone',
        mood_before='relax',
        mood_after='enjoyed',
        tags=[],
    )
    r = await async_client.get(
        f'/api/users/{me["id"]}/cards',
        params={'film_title': 'MATRIX'},
    )
    assert r.status_code == 200
    assert [x['id'] for x in r.json()['items']] == [c_matrix]

    r_empty = await async_client.get(
        f'/api/users/{me["id"]}/cards',
        params={'film_title': 'zz_no_such_title'},
    )
    assert r_empty.status_code == 200
    assert r_empty.json()['items'] == []


@pytest.mark.asyncio
async def test_list_user_cards_rating_pagination_cursor(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=5207)
    target = await _login(async_client, telegram_user_id=5208)
    uid = UUID(str(target['id']))

    for i, rating in enumerate([10.0, 9.0, 8.0, 7.0]):
        await _seed_movie_card(
            user_id=uid,
            kinopoisk_id=5208000 + i,
            title=f'R{i}',
            year=2020,
            rating=rating,
            company='alone',
            mood_after='enjoyed',
            tags=[],
        )

    first = await async_client.get(
        f'/api/users/{uid}/cards', params={'sort': 'rating_desc', 'limit': 2}
    )
    assert first.status_code == 200
    body1 = first.json()
    assert len(body1['items']) == 2
    assert body1['next_cursor'] is not None

    second = await async_client.get(
        f'/api/users/{uid}/cards',
        params={'sort': 'rating_desc', 'limit': 2, 'cursor': body1['next_cursor']},
    )
    assert second.status_code == 200
    ids_page1 = {x['id'] for x in body1['items']}
    ids_page2 = {x['id'] for x in second.json()['items']}
    assert ids_page1.isdisjoint(ids_page2)
