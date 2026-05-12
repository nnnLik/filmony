from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.api.test_cards_routes import _create_film, _login


@pytest.mark.asyncio
async def test_watched_inline_picker_requires_auth(async_client: AsyncClient) -> None:
    r = await async_client.get('/api/cards/watched-inline-picker')
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_watched_inline_picker_filters_by_query(async_client: AsyncClient) -> None:
    await _login(async_client, telegram_user_id=880_001)
    film = await _create_film(kinopoisk_id=880_101, title='ZetaUniquePickerTitle', year=2015)
    cr = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': [],
            'rating': 6.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert cr.status_code == 200
    r = await async_client.get(
        '/api/cards/watched-inline-picker',
        params={'q': 'ZetaUnique', 'limit': 20},
    )
    assert r.status_code == 200
    data = r.json()
    assert 'items' in data
    assert len(data['items']) >= 1
    hit = next((x for x in data['items'] if x['film_title'] == 'ZetaUniquePickerTitle'), None)
    assert hit is not None
    assert hit['movie_card_id'] == cr.json()['id']
    assert hit['film_year'] == 2015


@pytest.mark.asyncio
async def test_movie_card_comment_with_inline_card_ref_returns_snippets(
    async_client: AsyncClient,
) -> None:
    await _login(async_client, telegram_user_id=880_002)
    film = await _create_film(kinopoisk_id=880_102, title='InlineSnippetFilm', year=2001)
    cr = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': [],
            'rating': 5.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert cr.status_code == 200
    card_id = cr.json()['id']
    token = f'смотри⟦c{card_id}⟧'
    com = await async_client.post(
        f'/api/cards/{card_id}/comments',
        json={'text': token},
    )
    assert com.status_code == 200
    body = com.json()
    assert body['text'] == token
    assert len(body['referenced_movie_cards']) == 1
    ref0 = body['referenced_movie_cards'][0]
    assert ref0['movie_card_id'] == card_id
    assert ref0['film_title'] == 'InlineSnippetFilm'
    assert ref0['film_year'] == 2001


@pytest.mark.asyncio
async def test_movie_card_comment_rejects_inline_ref_to_foreign_card(
    async_client: AsyncClient,
) -> None:
    film = await _create_film(kinopoisk_id=880_103, title='OwnerFilm', year=2002)
    await _login(async_client, telegram_user_id=880_003)
    owner_card = await async_client.post(
        '/api/cards',
        json={
            'film_id': film.id,
            'kinopoisk_id': film.kinopoisk_id,
            'genres': [],
            'rating': 5.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert owner_card.status_code == 200
    owner_card_id = owner_card.json()['id']

    film2 = await _create_film(kinopoisk_id=880_104, title='StrangerFilm', year=2003)
    await _login(async_client, telegram_user_id=880_004)
    stranger_card = await async_client.post(
        '/api/cards',
        json={
            'film_id': film2.id,
            'kinopoisk_id': film2.kinopoisk_id,
            'genres': [],
            'rating': 6.0,
            'company': 'alone',
            'mood_before': 'relax',
            'mood_after': 'enjoyed',
            'custom_tags': [],
        },
    )
    assert stranger_card.status_code == 200

    bad = await async_client.post(
        f'/api/cards/{owner_card_id}/comments',
        json={'text': f'⟦c{owner_card_id}⟧'},
    )
    assert bad.status_code == 422
