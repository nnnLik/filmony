from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.controversy.schemas import WeeklyControversyItemResponse, WeeklyControversyResponse
from core.database import get_db
from deps.auth import CurrentUser
from services.controversy.get_current_week_controversy import GetCurrentWeekControversyService

router = APIRouter(prefix='/me', tags=['controversy'])


@router.get('/weekly-controversy', response_model=WeeklyControversyResponse)
async def get_my_weekly_controversy(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> WeeklyControversyResponse:
    result = await GetCurrentWeekControversyService.build(db).execute(viewer_user_id=user.id)
    controversy = result.controversy
    item = None
    if controversy is not None:
        item = WeeklyControversyItemResponse(
            anchor_film_id=controversy.anchor_film_id,
            anchor_catalog_item_id=controversy.anchor_catalog_item_id,
            title=controversy.title,
            spread=controversy.spread,
            rater_count=controversy.rater_count,
            min_rating=controversy.min_rating,
            max_rating=controversy.max_rating,
        )
    return WeeklyControversyResponse(week_start=result.week_start, controversy=item)
