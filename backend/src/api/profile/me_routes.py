from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.profile.schemas import (
    MyProfileResponse,
    ProfileUpdateRequest,
    build_my_profile_response,
)
from core.database import get_db
from deps.auth import CurrentUser
from services.profile.get_user_profile_counts import GetUserProfileCountsService
from services.profile.update_my_profile import (
    ProfileSlugInvalidError,
    ProfileSlugTakenError,
    UpdateMyProfileService,
)

router = APIRouter(prefix='/me', tags=['profile'])


@router.get(
    '/profile',
    response_model=MyProfileResponse,
    summary='Текущий пользователь: полный профиль для редактирования',
)
async def get_my_profile(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MyProfileResponse:
    counts = await GetUserProfileCountsService().execute(user.id)
    return build_my_profile_response(user, counts)


@router.patch(
    '/profile',
    response_model=MyProfileResponse,
    summary='Обновить поля своего профиля',
)
async def patch_my_profile(
    body: ProfileUpdateRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MyProfileResponse:
    patch = body.model_dump(exclude_unset=True)
    if not patch:
        counts = await GetUserProfileCountsService().execute(user.id)
        return build_my_profile_response(user, counts)

    try:
        updated = await UpdateMyProfileService(db).execute(user.id, patch)
    except ProfileSlugInvalidError:
        raise HTTPException(
            status_code=422,
            detail='profile_slug must be 3–32 chars: lowercase letters, digits, non-leading/trailing hyphen',
        ) from None
    except ProfileSlugTakenError:
        raise HTTPException(status_code=409, detail='profile_slug already taken') from None
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    counts = await GetUserProfileCountsService().execute(updated.id)
    return build_my_profile_response(updated, counts)
