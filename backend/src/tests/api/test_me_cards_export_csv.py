"""Tests for POST /api/me/cards/export-csv — mocked Telegram Bot API."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch
from uuid import UUID

import pytest
from httpx import AsyncClient

from conf import settings
from integrations.telegram.bot_api_client import TelegramBotApiClient, TelegramSendMessageResult
from tests.auth.telegram_init_data import build_init_data


def _document_bytes_from_send_document_mock(m: AsyncMock) -> bytes:
    args, kwargs = m.call_args
    if 'document_bytes' in kwargs:
        return kwargs['document_bytes']
    if len(args) >= 2 and isinstance(args[1], bytes):
        return args[1]
    if len(args) >= 3:
        return args[2]
    raise AssertionError(f'unexpected send_document_multipart call_args={m.call_args!r}')


@pytest.fixture
async def logged_in_client(async_client: AsyncClient) -> AsyncClient:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=992_001)
    login = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert login.status_code == 200
    return async_client


async def test_export_cards_csv_sent_empty_profile(logged_in_client: AsyncClient) -> None:
    with patch.object(TelegramBotApiClient, 'send_document_multipart', new_callable=AsyncMock) as m:
        m.return_value = TelegramSendMessageResult(ok=True, payload={'ok': True, 'result': {}})
        r = await logged_in_client.post('/api/me/cards/export-csv')

    assert r.status_code == 200
    assert r.json() == {'status': 'sent'}
    assert m.await_count == 1
    _, kwargs = m.call_args
    assert kwargs['filename'].endswith('.csv')
    assert kwargs['content_type'] == 'text/csv'
    doc_bytes = _document_bytes_from_send_document_mock(m)
    assert isinstance(doc_bytes, bytes)
    assert doc_bytes.startswith(b'\xef\xbb\xbf')  # UTF-8 BOM
    text_head = doc_bytes.decode('utf-8-sig')
    assert 'card_id' in text_head.splitlines()[0]


async def test_export_cards_csv_sent_with_row(logged_in_client: AsyncClient) -> None:
    prof = await logged_in_client.get('/api/me/profile')
    assert prof.status_code == 200
    user_id = UUID(prof.json()['id'])

    from core.database import get_session_factory
    from models.film import Film
    from models.movie_card import MovieCard
    from models.movie_card_tag import MovieCardTag

    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=9_920_002,
            title='Export, "Film"',
            year=2020,
            poster_url='https://example.com/x.jpg',
            genres=['drama', 'sci-fi'],
        )
        session.add(film)
        await session.flush()
        card = MovieCard(
            user_id=user_id,
            film_id=film.id,
            rating=8.5,
            company='solo',
            mood_before='low',
            mood_after='high',
        )
        session.add(card)
        await session.flush()
        session.add(MovieCardTag(movie_card_id=card.id, tag='cinema'))
        await session.commit()

    with patch.object(TelegramBotApiClient, 'send_document_multipart', new_callable=AsyncMock) as m:
        m.return_value = TelegramSendMessageResult(ok=True, payload={'ok': True, 'result': {}})
        r = await logged_in_client.post('/api/me/cards/export-csv')

    assert r.status_code == 200
    doc_bytes = _document_bytes_from_send_document_mock(m).decode('utf-8-sig')
    lines = doc_bytes.strip().splitlines()
    assert len(lines) >= 2
    data_line = lines[1]
    assert 'Export, "Film"' in data_line or 'Export,' in data_line
    assert 'drama|sci-fi' in data_line
    assert 'cinema' in data_line


async def test_export_cards_csv_chat_unavailable(logged_in_client: AsyncClient) -> None:
    with patch.object(TelegramBotApiClient, 'send_document_multipart', new_callable=AsyncMock) as m:
        m.return_value = TelegramSendMessageResult(
            ok=False,
            payload={
                'ok': False,
                'error_code': 403,
                'description': "Forbidden: bot can't initiate conversation with the user",
            },
        )
        r = await logged_in_client.post('/api/me/cards/export-csv')

    assert r.status_code == 422
    detail = r.json()['detail']
    assert detail['code'] == 'telegram_chat_unavailable'
    assert 'bot_username' in detail


async def test_export_cards_csv_telegram_other_error(logged_in_client: AsyncClient) -> None:
    with patch.object(TelegramBotApiClient, 'send_document_multipart', new_callable=AsyncMock) as m:
        m.return_value = TelegramSendMessageResult(
            ok=False,
            payload={'ok': False, 'error_code': 500, 'description': 'internal telegram glitch'},
        )
        r = await logged_in_client.post('/api/me/cards/export-csv')

    assert r.status_code == 502
    assert r.json()['detail']['code'] == 'telegram_delivery_failed'
