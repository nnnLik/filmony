from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.taste_quiz.schemas import (
    TasteQuizCanPlayResponse,
    TasteQuizCreateInviteResponse,
    TasteQuizCreateSessionRequest,
    TasteQuizInviteOwnerSnippetResponse,
    TasteQuizKnowledgeBatchItemResponse,
    TasteQuizKnowledgeBatchRequest,
    TasteQuizKnowledgeBatchResponse,
    TasteQuizKnowledgeItemResponse,
    TasteQuizKnowledgeListResponse,
    TasteQuizPairProgressResponse,
    TasteQuizResolveInviteResponse,
    TasteQuizSessionCardResponse,
    TasteQuizSessionResponse,
    TasteQuizSubmitAnswerRequest,
    TasteQuizSubmitAnswerResponse,
)
from celery_app import app as celery_application
from core.database import get_db
from deps.auth import CurrentUser
from services.taste_quiz.abandon_session import AbandonTasteQuizSessionService
from services.taste_quiz.batch_knowledge import BatchTasteQuizKnowledgeService
from services.taste_quiz.check_can_play import CheckTasteQuizCanPlayService
from services.taste_quiz.create_invite import CreateTasteQuizInviteService
from services.taste_quiz.create_session import CreateTasteQuizSessionService
from services.taste_quiz.get_session import GetTasteQuizSessionService
from services.taste_quiz.list_knowledge import (
    ListTasteQuizKnowledgeService,
    TasteQuizKnowledgeDirection,
)
from services.taste_quiz.resolve_invite import ResolveTasteQuizInviteService
from services.taste_quiz.session_mapper import TasteQuizSessionCardDTO, TasteQuizSessionDTO
from services.taste_quiz.submit_answer import SubmitTasteQuizAnswerService

router = APIRouter(prefix='/taste-quiz', tags=['taste-quiz'])


def _session_card_response(card: TasteQuizSessionCardDTO) -> TasteQuizSessionCardResponse:
    return TasteQuizSessionCardResponse(
        session_card_id=card.session_card_id,
        card_id=card.card_id,
        order_index=card.order_index,
        title=card.title,
        poster_url=card.poster_url,
        company=card.company,
        mood_before=card.mood_before,
        owner_rating=card.owner_rating,
        mood_after=card.mood_after,
        watch_note=card.watch_note,
        guess_rating=card.guess_rating,
        round_points=card.round_points,
        verdict_key=card.verdict_key,
        answered_at=card.answered_at,
    )


def _session_response(session: TasteQuizSessionDTO) -> TasteQuizSessionResponse:
    return TasteQuizSessionResponse(
        id=session.id,
        guesser_user_id=session.guesser_user_id,
        owner_user_id=session.owner_user_id,
        status=session.status.value,
        card_count=session.card_count,
        current_index=session.current_index,
        round_points=session.round_points,
        cards=[_session_card_response(card) for card in session.cards],
        created_at=session.created_at,
        completed_at=session.completed_at,
    )


@router.get('/can-play', response_model=TasteQuizCanPlayResponse)
async def check_can_play(
    owner_id: UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    invite_token: str | None = Query(default=None),
) -> TasteQuizCanPlayResponse:
    service = CheckTasteQuizCanPlayService.build(db)
    try:
        outcome = await service.execute(
            guesser_user_id=user.id,
            owner_user_id=owner_id,
            invite_token=invite_token,
        )
    except CheckTasteQuizCanPlayService.SelfPlayError:
        raise HTTPException(status_code=422, detail='cannot play against yourself') from None
    except CheckTasteQuizCanPlayService.OwnerNotFoundError:
        raise HTTPException(status_code=404, detail='owner not found') from None
    return TasteQuizCanPlayResponse(
        can_play=outcome.can_play,
        reason=outcome.reason,
        owner_rated_count=outcome.owner_rated_count,
        requires_follow=outcome.requires_follow,
        guesser_follows_owner=outcome.guesser_follows_owner,
        active_session_id=outcome.active_session_id,
        gate_min_rated_cards=outcome.gate_min_rated_cards,
    )


@router.post('/sessions', response_model=TasteQuizSessionResponse, status_code=status.HTTP_201_CREATED)
async def create_session(
    body: TasteQuizCreateSessionRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TasteQuizSessionResponse:
    service = CreateTasteQuizSessionService.build(db)
    try:
        session = await service.execute(
            guesser_user_id=user.id,
            owner_user_id=body.owner_id,
            invite_token=body.invite_token,
        )
    except CreateTasteQuizSessionService.SelfPlayError:
        raise HTTPException(status_code=422, detail='cannot play against yourself') from None
    except CreateTasteQuizSessionService.OwnerNotFoundError:
        raise HTTPException(status_code=404, detail='owner not found') from None
    except CreateTasteQuizSessionService.GateError:
        raise HTTPException(status_code=422, detail='owner has insufficient rated cards') from None
    except CreateTasteQuizSessionService.NotFollowingError:
        raise HTTPException(status_code=403, detail='must follow owner') from None
    except CreateTasteQuizSessionService.ActiveSessionExistsError as exc:
        raise HTTPException(
            status_code=409,
            detail={'message': 'active session exists', 'session_id': str(exc.session_id)},
        ) from None
    return _session_response(session)


@router.get('/sessions/{session_id}', response_model=TasteQuizSessionResponse)
async def get_session(
    session_id: UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TasteQuizSessionResponse:
    service = GetTasteQuizSessionService.build(db)
    try:
        session = await service.execute(guesser_user_id=user.id, session_id=session_id)
    except GetTasteQuizSessionService.SessionNotFoundError:
        raise HTTPException(status_code=404, detail='session not found') from None
    except GetTasteQuizSessionService.ForbiddenError:
        raise HTTPException(status_code=403, detail='forbidden') from None
    return _session_response(session)


@router.post('/sessions/{session_id}/answers', response_model=TasteQuizSubmitAnswerResponse)
async def submit_answer(
    session_id: UUID,
    body: TasteQuizSubmitAnswerRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TasteQuizSubmitAnswerResponse:
    service = SubmitTasteQuizAnswerService.build(db)
    try:
        outcome = await service.execute(
            guesser_user_id=user.id,
            session_id=session_id,
            session_card_id=body.session_card_id,
            guess_rating=body.guess_rating,
        )
    except SubmitTasteQuizAnswerService.SessionNotFoundError:
        raise HTTPException(status_code=404, detail='session not found') from None
    except SubmitTasteQuizAnswerService.ForbiddenError:
        raise HTTPException(status_code=403, detail='forbidden') from None
    except SubmitTasteQuizAnswerService.SessionNotActiveError:
        raise HTTPException(status_code=409, detail='session not active') from None
    except SubmitTasteQuizAnswerService.CardNotFoundError:
        raise HTTPException(status_code=404, detail='session card not found') from None
    except SubmitTasteQuizAnswerService.AlreadyAnsweredError:
        raise HTTPException(status_code=409, detail='already answered') from None
    except SubmitTasteQuizAnswerService.WrongCardOrderError:
        raise HTTPException(status_code=400, detail='wrong card order') from None
    except SubmitTasteQuizAnswerService.InvalidRatingError:
        raise HTTPException(status_code=400, detail='invalid rating') from None

    if outcome.session_completed:
        celery_application.tasks[
            'tasks.telegram_engagement.deliver_taste_quiz_complete_notification'
        ].delay(
            session_id=str(session_id),
            owner_user_id=str(outcome.session.owner_user_id),
            guesser_user_id=str(user.id),
            round_points=str(outcome.session.round_points),
        )

    return TasteQuizSubmitAnswerResponse(
        card=_session_card_response(outcome.card),
        session=_session_response(outcome.session),
        pair_progress=TasteQuizPairProgressResponse(
            points_sum=float(outcome.pair_progress['points_sum']),
            attempts=int(outcome.pair_progress['attempts']),
            accuracy_pct=int(outcome.pair_progress['accuracy_pct']),
        ),
        session_completed=outcome.session_completed,
    )


@router.post('/sessions/{session_id}/abandon', response_model=TasteQuizSessionResponse)
async def abandon_session(
    session_id: UUID,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TasteQuizSessionResponse:
    service = AbandonTasteQuizSessionService.build(db)
    try:
        session = await service.execute(guesser_user_id=user.id, session_id=session_id)
    except AbandonTasteQuizSessionService.SessionNotFoundError:
        raise HTTPException(status_code=404, detail='session not found') from None
    except AbandonTasteQuizSessionService.ForbiddenError:
        raise HTTPException(status_code=403, detail='forbidden') from None
    except AbandonTasteQuizSessionService.SessionNotActiveError:
        raise HTTPException(status_code=409, detail='session not active') from None
    return _session_response(session)


@router.get('/knowledge', response_model=TasteQuizKnowledgeListResponse)
async def list_knowledge(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    direction: TasteQuizKnowledgeDirection = Query(default=TasteQuizKnowledgeDirection.TO_THEM),
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
) -> TasteQuizKnowledgeListResponse:
    outcome = await ListTasteQuizKnowledgeService.build(db).execute(
        viewer_user_id=user.id,
        direction=direction,
        cursor=cursor,
        limit=limit,
    )
    return TasteQuizKnowledgeListResponse(
        items=[
            TasteQuizKnowledgeItemResponse(
                user_id=item.user_id,
                profile_slug=item.profile_slug,
                display_name=item.display_name,
                avatar_url=item.avatar_url,
                points_sum=item.points_sum,
                attempts=item.attempts,
                accuracy_pct=item.accuracy_pct,
            )
            for item in outcome.items
        ],
        next_cursor=outcome.next_cursor,
    )


@router.post('/knowledge/batch', response_model=TasteQuizKnowledgeBatchResponse)
async def batch_knowledge(
    body: TasteQuizKnowledgeBatchRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TasteQuizKnowledgeBatchResponse:
    _ = user
    items = await BatchTasteQuizKnowledgeService.build(db).execute(
        owner_user_id=body.owner_id,
        guesser_user_ids=list(body.guesser_user_ids),
    )
    return TasteQuizKnowledgeBatchResponse(
        items={
            str(user_id): TasteQuizKnowledgeBatchItemResponse(
                attempts=item.attempts,
                accuracy_pct=item.accuracy_pct,
                points_sum=item.points_sum,
            )
            for user_id, item in items.items()
        }
    )


@router.post('/invites', response_model=TasteQuizCreateInviteResponse, status_code=status.HTTP_201_CREATED)
async def create_invite(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TasteQuizCreateInviteResponse:
    outcome = await CreateTasteQuizInviteService.build(db).execute(owner_user_id=user.id)
    return TasteQuizCreateInviteResponse(
        invite_token=outcome.invite_token,
        share_url=outcome.share_url,
        telegram_share_text=outcome.telegram_share_text,
    )


@router.get('/invites/{token}', response_model=TasteQuizResolveInviteResponse)
async def resolve_invite(
    token: str,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> TasteQuizResolveInviteResponse:
    service = ResolveTasteQuizInviteService.build(db)
    try:
        outcome = await service.execute(invite_token=token, guesser_user_id=user.id)
    except ResolveTasteQuizInviteService.InviteNotFoundError:
        raise HTTPException(status_code=404, detail='invite not found') from None
    return TasteQuizResolveInviteResponse(
        owner=TasteQuizInviteOwnerSnippetResponse(
            user_id=outcome.owner.user_id,
            profile_slug=outcome.owner.profile_slug,
            display_name=outcome.owner.display_name,
            avatar_url=outcome.owner.avatar_url,
        ),
        invite_token=outcome.invite_token,
        share_url=outcome.share_url,
        can_play=outcome.can_play,
        reason=outcome.reason,
        owner_rated_count=outcome.owner_rated_count,
        gate_min_rated_cards=outcome.gate_min_rated_cards,
        expired=outcome.expired,
    )
