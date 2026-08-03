from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.gamification.schemas import (
    GamificationResponse,
    MarathonAchievementResponse,
    PassportResponse,
    PassportStampResponse,
    PublicPassportResponse,
    ShelfPhysicsResponse,
)
from core.database import get_db
from deps.auth import CurrentUser
from services.gamification.compute_marathon_achievements import ComputeMarathonAchievementsService
from services.gamification.compute_passport_stamps import (
    ComputePassportStampsService,
    PassportStampDTO,
)
from services.gamification.compute_shelf_physics import ComputeShelfPhysicsService
from services.profile.get_public_user_by_id import GetPublicUserByIdService

router = APIRouter(tags=['gamification'])


def _stamp_to_response(stamp: PassportStampDTO) -> PassportStampResponse:
    return PassportStampResponse(
        stamp_id=stamp.stamp_id,
        title=stamp.title,
        description=stamp.description,
        unlocked=stamp.unlocked,
        unlocked_at=stamp.unlocked_at,
        progress_current=stamp.progress_current,
        progress_target=stamp.progress_target,
        unlock_card_id=stamp.unlock_card_id,
        unlock_film_title=stamp.unlock_film_title,
        unlock_film_poster_url=stamp.unlock_film_poster_url,
    )


@router.get('/me/gamification', response_model=GamificationResponse)
async def get_my_gamification(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> GamificationResponse:
    passport = await ComputePassportStampsService.build(db).execute(user.id)
    marathons = await ComputeMarathonAchievementsService.build(db).execute(user.id)
    shelf = await ComputeShelfPhysicsService.build(db).execute(user.id)
    return GamificationResponse(
        passport=PassportResponse(
            stamps=[_stamp_to_response(stamp) for stamp in passport.stamps],
            unlocked_count=passport.unlocked_count,
        ),
        marathons=[
            MarathonAchievementResponse(
                kind=item.kind,
                key=item.key,
                label=item.label,
                count=item.count,
                unlocked_at=item.unlocked_at,
                sample_poster_urls=list(item.sample_poster_urls),
            )
            for item in marathons
        ],
        shelf_physics=ShelfPhysicsResponse(
            mode=shelf.mode,
            streak_length=shelf.streak_length,
        ),
    )


@router.get(
    '/users/{user_id}/gamification/passport',
    response_model=PublicPassportResponse,
    summary='Публичные штампы паспорта (только unlocked)',
)
async def get_user_gamification_passport(
    user_id: UUID,
    _viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> PublicPassportResponse:
    target = await GetPublicUserByIdService(db).execute(user_id)
    if target is None:
        raise HTTPException(status_code=404, detail='user not found')
    passport = await ComputePassportStampsService.build(db).execute(user_id)
    unlocked = [stamp for stamp in passport.stamps if stamp.unlocked]
    return PublicPassportResponse(
        stamps=[_stamp_to_response(stamp) for stamp in unlocked],
        unlocked_count=len(unlocked),
    )
