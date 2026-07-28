from __future__ import annotations

from typing import Annotated

from api.streaks.schemas import (
    STREAK_BATCH_MIN_CURRENT,
    MyStreakResponse,
    StreakBatchRequest,
    StreakBatchResponse,
    StreakItemResponse,
)
from core.database import get_db
from deps.auth import CurrentUser
from fastapi import APIRouter, Depends
from services.streaks.batch_user_rating_streaks import BatchUserRatingStreaksService
from sqlalchemy.ext.asyncio import AsyncSession

streaks_router = APIRouter(prefix='/streaks', tags=['streaks'])
me_streak_router = APIRouter(prefix='/me', tags=['streaks'])


@streaks_router.post('/batch', response_model=StreakBatchResponse)
async def batch_streaks(
    body: StreakBatchRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> StreakBatchResponse:
    _ = user
    items = await BatchUserRatingStreaksService.build(db).execute(
        list(body.user_ids),
        min_current=STREAK_BATCH_MIN_CURRENT,
    )
    return StreakBatchResponse(
        items={
            str(user_id): StreakItemResponse(current=item.current)
            for user_id, item in items.items()
        }
    )


@me_streak_router.get('/streak', response_model=MyStreakResponse)
async def get_my_streak(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MyStreakResponse:
    items = await BatchUserRatingStreaksService.build(db).execute([user.id])
    item = items.get(user.id)
    return MyStreakResponse(current=0 if item is None else item.current)
