from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.reactions.schemas import (
    ReactionCatalogItemResponse,
    ReactionCatalogListResponse,
    UserReactionSetRequest,
    UserReactionSetResponse,
    reaction_target_summary_to_response,
)
from core.database import get_db
from deps.auth import CurrentUser
from models.reaction_target_kind import ReactionTargetKind
from services.reactions.list_reaction_catalog import ListReactionCatalogService
from services.reactions.set_or_toggle_user_reaction import (
    ReactionTargetNotFoundError,
    ReactionTypeInvalidError,
    SelfReactionForbiddenError,
    SetOrToggleUserReactionService,
    SetUserReactionInput,
)

router = APIRouter(prefix='/reactions', tags=['reactions'])


def _parse_target_kind(raw: str) -> ReactionTargetKind:
    try:
        return ReactionTargetKind(raw)
    except ValueError:
        raise HTTPException(status_code=422, detail='invalid target_kind') from None


@router.get('/catalog', response_model=ReactionCatalogListResponse, summary='Каталог реакций')
async def list_reaction_catalog(
    _user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ReactionCatalogListResponse:
    rows = await ListReactionCatalogService(db).execute()
    return ReactionCatalogListResponse(
        items=[
            ReactionCatalogItemResponse(id=r.id, label=r.label, image_url=r.image_url) for r in rows
        ]
    )


@router.post('', response_model=UserReactionSetResponse, summary='Поставить или снять реакцию')
async def set_user_reaction(
    body: UserReactionSetRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserReactionSetResponse:
    kind = _parse_target_kind(body.target_kind)
    try:
        summary = await SetOrToggleUserReactionService(db).execute(
            user.id,
            SetUserReactionInput(
                target_kind=kind,
                target_id=body.target_id,
                reaction_type_id=body.reaction_type_id,
            ),
        )
    except ReactionTypeInvalidError:
        raise HTTPException(status_code=422, detail='invalid reaction_type_id') from None
    except ReactionTargetNotFoundError:
        raise HTTPException(status_code=404, detail='target not found') from None
    except SelfReactionForbiddenError:
        raise HTTPException(status_code=403, detail='self reaction not allowed') from None

    return UserReactionSetResponse(
        target_kind=kind.value,
        target_id=body.target_id,
        reactions=reaction_target_summary_to_response(summary),
    )
