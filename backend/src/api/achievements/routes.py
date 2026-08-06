from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from api.achievements.schemas import (
    MyAchievementsListResponse,
    SetAchievementPinsRequest,
    build_my_achievements_list_response,
)
from core.database import get_db
from deps.auth import CurrentUser
from services.achievements.list_user_achievements import ListUserAchievementsService
from services.achievements.set_user_achievement_pins import SetUserAchievementPinsService

router = APIRouter(prefix='/me', tags=['achievements'])


@router.get('/achievements', response_model=MyAchievementsListResponse)
async def list_my_achievements(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MyAchievementsListResponse:
    items = await ListUserAchievementsService.build(db).execute(user.id)
    return build_my_achievements_list_response(items)


@router.put('/achievement-pins', status_code=204)
async def set_my_achievement_pins(
    body: SetAchievementPinsRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    service = SetUserAchievementPinsService.build(db)
    try:
        await service.execute(user.id, body.achievement_slugs)
    except SetUserAchievementPinsService.TooManyPins:
        raise HTTPException(status_code=400, detail='max 3 achievement pins allowed') from None
    except SetUserAchievementPinsService.DuplicateSlug:
        raise HTTPException(status_code=400, detail='duplicate achievement slug') from None
    except SetUserAchievementPinsService.AchievementNotFound:
        raise HTTPException(status_code=404, detail='achievement not found') from None
    except SetUserAchievementPinsService.AchievementNotUnlocked:
        raise HTTPException(status_code=400, detail='achievement not unlocked') from None
    return Response(status_code=204)
