"""Taste quiz API routes."""

from __future__ import annotations

from unittest.mock import MagicMock
from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from celery_app import app as celery_app_instance
from conf import settings
from core.database import get_session_factory
from models.taste_quiz_pair_progress import TasteQuizPairProgress
from models.taste_quiz_session_card import TasteQuizSessionCard
from models.user_card import UserCard
from tests.auth.telegram_init_data import build_init_data
from tests.support.taste_quiz_helpers import add_follow, seed_rated_cards_for_owner


async def _login(async_client: AsyncClient, telegram_user_id: int) -> dict[str, object]:
    init = build_init_data(bot_token=settings.telegram.bot_token, user_id=telegram_user_id)
    response = await async_client.post('/api/auth/telegram', json={'initData': init})
    assert response.status_code == 200
    return response.json()


@pytest.mark.asyncio
async def test_can_play_gate_when_owner_has_few_cards(async_client: AsyncClient) -> None:
    owner = await _login(async_client, telegram_user_id=920001)
    guesser = await _login(async_client, telegram_user_id=920002)
    await add_follow(
        follower_user_id=UUID(str(guesser['id'])),
        following_user_id=UUID(str(owner['id'])),
    )
    await seed_rated_cards_for_owner(
        owner_user_id=UUID(str(owner['id'])),
        count=5,
        kinopoisk_id_base=920_100,
    )

    response = await async_client.get(
        '/api/taste-quiz/can-play',
        params={'owner_id': owner['id']},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload['can_play'] is False
    assert payload['reason'] == 'owner_insufficient_cards'
    assert payload['owner_rated_count'] == 5


@pytest.mark.asyncio
async def test_can_play_requires_follow_without_invite(async_client: AsyncClient) -> None:
    owner = await _login(async_client, telegram_user_id=920011)
    await _login(async_client, telegram_user_id=920012)
    await seed_rated_cards_for_owner(
        owner_user_id=UUID(str(owner['id'])),
        count=10,
        kinopoisk_id_base=920_200,
    )

    response = await async_client.get(
        '/api/taste-quiz/can-play',
        params={'owner_id': owner['id']},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload['can_play'] is False
    assert payload['reason'] == 'not_following'
    assert payload['requires_follow'] is True


@pytest.mark.asyncio
async def test_create_session_and_submit_answer(async_client: AsyncClient) -> None:
    owner = await _login(async_client, telegram_user_id=920021)
    guesser = await _login(async_client, telegram_user_id=920022)
    owner_id = UUID(str(owner['id']))
    guesser_id = UUID(str(guesser['id']))
    await add_follow(follower_user_id=guesser_id, following_user_id=owner_id)
    await seed_rated_cards_for_owner(owner_user_id=owner_id, count=10, kinopoisk_id_base=920_300)

    create_response = await async_client.post(
        '/api/taste-quiz/sessions',
        json={'owner_id': str(owner_id)},
    )
    assert create_response.status_code == 201
    session_payload = create_response.json()
    assert session_payload['status'] == 'active'
    assert session_payload['card_count'] == 10
    assert session_payload['current_index'] == 0
    first_card = session_payload['cards'][0]
    assert first_card['owner_rating'] is None
    assert first_card['mood_after'] is None
    assert first_card['watch_note'] is None

    session_factory = get_session_factory()
    async with session_factory() as session:
        db_card = await session.get(
            TasteQuizSessionCard,
            UUID(str(first_card['session_card_id'])),
        )
        assert db_card is not None
        owner_rating = float(db_card.snapshot_owner_rating)

    answer_response = await async_client.post(
        f"/api/taste-quiz/sessions/{session_payload['id']}/answers",
        json={
            'session_card_id': first_card['session_card_id'],
            'guess_rating': owner_rating,
        },
    )
    assert answer_response.status_code == 200
    answer_payload = answer_response.json()
    assert answer_payload['card']['round_points'] == 1.0
    assert answer_payload['card']['verdict_key'] == 'exact'
    assert answer_payload['card']['owner_rating'] == owner_rating
    assert answer_payload['card']['mood_after'] is not None
    assert answer_payload['session']['current_index'] == 1
    assert answer_payload['pair_progress']['attempts'] == 1
    assert answer_payload['pair_progress']['points_sum'] == 1.0


@pytest.mark.asyncio
async def test_create_session_conflict_when_active_exists(async_client: AsyncClient) -> None:
    owner = await _login(async_client, telegram_user_id=920031)
    guesser = await _login(async_client, telegram_user_id=920032)
    owner_id = UUID(str(owner['id']))
    guesser_id = UUID(str(guesser['id']))
    await add_follow(follower_user_id=guesser_id, following_user_id=owner_id)
    await seed_rated_cards_for_owner(owner_user_id=owner_id, count=10, kinopoisk_id_base=920_400)

    first = await async_client.post('/api/taste-quiz/sessions', json={'owner_id': str(owner_id)})
    assert first.status_code == 201
    second = await async_client.post('/api/taste-quiz/sessions', json={'owner_id': str(owner_id)})
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_get_session_for_resume(async_client: AsyncClient) -> None:
    owner = await _login(async_client, telegram_user_id=920041)
    guesser = await _login(async_client, telegram_user_id=920042)
    owner_id = UUID(str(owner['id']))
    guesser_id = UUID(str(guesser['id']))
    await add_follow(follower_user_id=guesser_id, following_user_id=owner_id)
    await seed_rated_cards_for_owner(owner_user_id=owner_id, count=10, kinopoisk_id_base=920_500)

    created = await async_client.post('/api/taste-quiz/sessions', json={'owner_id': str(owner_id)})
    session_id = created.json()['id']
    resume = await async_client.get(f'/api/taste-quiz/sessions/{session_id}')
    assert resume.status_code == 200
    assert resume.json()['id'] == session_id


@pytest.mark.asyncio
async def test_abandon_session(async_client: AsyncClient) -> None:
    owner = await _login(async_client, telegram_user_id=920051)
    guesser = await _login(async_client, telegram_user_id=920052)
    owner_id = UUID(str(owner['id']))
    guesser_id = UUID(str(guesser['id']))
    await add_follow(follower_user_id=guesser_id, following_user_id=owner_id)
    await seed_rated_cards_for_owner(owner_user_id=owner_id, count=10, kinopoisk_id_base=920_600)

    created = await async_client.post('/api/taste-quiz/sessions', json={'owner_id': str(owner_id)})
    session_id = created.json()['id']
    abandoned = await async_client.post(f'/api/taste-quiz/sessions/{session_id}/abandon')
    assert abandoned.status_code == 200
    assert abandoned.json()['status'] == 'abandoned'


@pytest.mark.asyncio
async def test_invite_flow_bypasses_follow(async_client: AsyncClient) -> None:
    owner = await _login(async_client, telegram_user_id=920061)
    owner_id = UUID(str(owner['id']))
    await seed_rated_cards_for_owner(owner_user_id=owner_id, count=10, kinopoisk_id_base=920_700)

    invite_response = await async_client.post('/api/taste-quiz/invites')
    assert invite_response.status_code == 201
    invite_payload = invite_response.json()
    assert invite_payload['invite_token']
    assert invite_payload['share_url'] is not None
    assert 'startapp=tq' in invite_payload['share_url']

    await _login(async_client, telegram_user_id=920062)

    can_play = await async_client.get(
        '/api/taste-quiz/can-play',
        params={'owner_id': str(owner_id), 'invite_token': invite_payload['invite_token']},
    )
    assert can_play.status_code == 200
    assert can_play.json()['can_play'] is True
    assert can_play.json()['requires_follow'] is False

    create = await async_client.post(
        '/api/taste-quiz/sessions',
        json={'owner_id': str(owner_id), 'invite_token': invite_payload['invite_token']},
    )
    assert create.status_code == 201


@pytest.mark.asyncio
async def test_knowledge_batch_omits_zero_attempts(async_client: AsyncClient) -> None:
    owner = await _login(async_client, telegram_user_id=920071)
    guesser = await _login(async_client, telegram_user_id=920072)
    stranger = await _login(async_client, telegram_user_id=920073)
    owner_id = UUID(str(owner['id']))
    guesser_id = UUID(str(guesser['id']))
    stranger_id = UUID(str(stranger['id']))
    await add_follow(follower_user_id=guesser_id, following_user_id=owner_id)
    await seed_rated_cards_for_owner(owner_user_id=owner_id, count=10, kinopoisk_id_base=920_800)

    await _login(async_client, telegram_user_id=920072)

    created = await async_client.post('/api/taste-quiz/sessions', json={'owner_id': str(owner_id)})
    assert created.status_code == 201
    session = created.json()
    first_card = session['cards'][0]
    session_factory = get_session_factory()
    async with session_factory() as db:
        db_card = await db.get(TasteQuizSessionCard, UUID(str(first_card['session_card_id'])))
        assert db_card is not None
        owner_rating = float(db_card.snapshot_owner_rating)
    await async_client.post(
        f"/api/taste-quiz/sessions/{session['id']}/answers",
        json={'session_card_id': first_card['session_card_id'], 'guess_rating': owner_rating},
    )

    batch = await async_client.post(
        '/api/taste-quiz/knowledge/batch',
        json={
            'owner_id': str(owner_id),
            'guesser_user_ids': [str(guesser_id), str(stranger_id)],
        },
    )
    assert batch.status_code == 200
    items = batch.json()['items']
    assert str(guesser_id) in items
    assert str(stranger_id) not in items


@pytest.mark.asyncio
async def test_complete_session_queues_telegram_task(
    async_client: AsyncClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    mock_delay = MagicMock()
    notify_task = celery_app_instance.tasks[
        'tasks.telegram_engagement.deliver_taste_quiz_complete_notification'
    ]
    monkeypatch.setattr(notify_task, 'delay', mock_delay)

    owner = await _login(async_client, telegram_user_id=920081)
    guesser = await _login(async_client, telegram_user_id=920082)
    owner_id = UUID(str(owner['id']))
    guesser_id = UUID(str(guesser['id']))
    await add_follow(follower_user_id=guesser_id, following_user_id=owner_id)
    await seed_rated_cards_for_owner(owner_user_id=owner_id, count=10, kinopoisk_id_base=920_900)

    created = await async_client.post('/api/taste-quiz/sessions', json={'owner_id': str(owner_id)})
    assert created.status_code == 201
    session = created.json()

    for card in session['cards']:
        session_factory = get_session_factory()
        async with session_factory() as db:
            db_card = await db.get(TasteQuizSessionCard, UUID(str(card['session_card_id'])))
            assert db_card is not None
            owner_rating = float(db_card.snapshot_owner_rating)
        response = await async_client.post(
            f"/api/taste-quiz/sessions/{session['id']}/answers",
            json={'session_card_id': card['session_card_id'], 'guess_rating': owner_rating},
        )
        assert response.status_code == 200

    assert mock_delay.called
    assert response.json()['session_completed'] is True
    assert response.json()['session']['status'] == 'completed'


@pytest.mark.asyncio
async def test_snapshot_immutable_after_owner_card_edit(async_client: AsyncClient) -> None:
    owner = await _login(async_client, telegram_user_id=920091)
    guesser = await _login(async_client, telegram_user_id=920092)
    owner_id = UUID(str(owner['id']))
    guesser_id = UUID(str(guesser['id']))
    await add_follow(follower_user_id=guesser_id, following_user_id=owner_id)
    await seed_rated_cards_for_owner(
        owner_user_id=owner_id,
        count=10,
        kinopoisk_id_base=921_000,
        rating=6.0,
    )

    created = await async_client.post('/api/taste-quiz/sessions', json={'owner_id': str(owner_id)})
    assert created.status_code == 201
    session = created.json()
    first_card = session['cards'][0]
    original_card_id = first_card['card_id']

    session_factory = get_session_factory()
    async with session_factory() as db:
        live_card = await db.get(UserCard, original_card_id)
        assert live_card is not None
        live_card.rating = 10.0
        live_card.mood_after = 'cried'
        await db.commit()

    async with session_factory() as db:
        snapshot = await db.get(TasteQuizSessionCard, UUID(str(first_card['session_card_id'])))
        assert snapshot is not None
        assert float(snapshot.snapshot_owner_rating) == 6.0
        assert snapshot.snapshot_mood_after == 'enjoyed'

    answer = await async_client.post(
        f"/api/taste-quiz/sessions/{session['id']}/answers",
        json={'session_card_id': first_card['session_card_id'], 'guess_rating': 6.0},
    )
    assert answer.status_code == 200
    assert answer.json()['card']['owner_rating'] == 6.0


@pytest.mark.asyncio
async def test_played_card_ids_reset_when_unused_below_ten(async_client: AsyncClient) -> None:
    owner = await _login(async_client, telegram_user_id=920101)
    guesser = await _login(async_client, telegram_user_id=920102)
    owner_id = UUID(str(owner['id']))
    guesser_id = UUID(str(guesser['id']))
    await add_follow(follower_user_id=guesser_id, following_user_id=owner_id)
    card_ids = await seed_rated_cards_for_owner(
        owner_user_id=owner_id,
        count=12,
        kinopoisk_id_base=921_100,
    )

    session_factory = get_session_factory()
    async with session_factory() as db:
        progress = TasteQuizPairProgress(
            guesser_user_id=guesser_id,
            owner_user_id=owner_id,
            points_sum=0.0,
            attempts=0,
            played_card_ids=card_ids[:3],
        )
        db.add(progress)
        await db.commit()

    created = await async_client.post('/api/taste-quiz/sessions', json={'owner_id': str(owner_id)})
    assert created.status_code == 201
    assert len(created.json()['cards']) == 10

    async with session_factory() as db:
        row = (
            await db.execute(
                select(TasteQuizPairProgress).where(
                    TasteQuizPairProgress.guesser_user_id == guesser_id,
                    TasteQuizPairProgress.owner_user_id == owner_id,
                )
            )
        ).scalar_one()
        assert row.played_card_ids == []
