from __future__ import annotations

from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.search.schemas import (
    SearchCardItemResponse,
    SearchCatalogResponse,
    SearchSuggestionsResponse,
    SearchUserItemResponse,
)
from core.database import get_db
from deps.auth import CurrentUser
from services.search.search_catalog_cards import SearchCatalogCardsService
from services.search.search_catalog_users import SearchCatalogUsersService
from services.search.search_user_suggestions import SearchUserSuggestionsService

router = APIRouter(prefix='/search', tags=['search'])

_SEARCH_Q_MIN = 2
_SEARCH_Q_MAX = 64
_LIMIT_DEFAULT = 15
_LIMIT_MAX = 30


def _clamp_limit(value: int | None) -> int:
    if value is None:
        return _LIMIT_DEFAULT
    return max(1, min(value, _LIMIT_MAX))


@router.get('', response_model=SearchCatalogResponse)
async def search_catalog(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    q: Annotated[str, Query(min_length=1, max_length=128)],
    limit_cards: Annotated[int | None, Query(ge=1, le=_LIMIT_MAX)] = None,
    limit_films: Annotated[int | None, Query(ge=1, le=_LIMIT_MAX)] = None,
    limit_users: Annotated[int | None, Query(ge=1, le=_LIMIT_MAX)] = None,
) -> SearchCatalogResponse:
    query = q.strip()
    if len(query) < _SEARCH_Q_MIN:
        raise HTTPException(
            status_code=422,
            detail=f'query must be at least {_SEARCH_Q_MIN} characters after trimming',
        )
    if len(query) > _SEARCH_Q_MAX:
        raise HTTPException(
            status_code=422,
            detail=f'query must be at most {_SEARCH_Q_MAX} characters after trimming',
        )

    lc = _clamp_limit(limit_cards if limit_cards is not None else limit_films)
    lu = _clamp_limit(limit_users)

    cards = await SearchCatalogCardsService.build(db).execute(query, lc)
    users = await SearchCatalogUsersService.build(db).execute(query, lu)
    serialized_cards = [SearchCardItemResponse(**asdict(c)) for c in cards]

    return SearchCatalogResponse(
        cards=serialized_cards,
        films=serialized_cards,
        users=[SearchUserItemResponse(**asdict(u)) for u in users],
    )


@router.get('/suggestions', response_model=SearchSuggestionsResponse)
async def search_suggestions(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> SearchSuggestionsResponse:
    result = await SearchUserSuggestionsService.build(db).execute(user.id)
    return SearchSuggestionsResponse(
        mutual_circle=[SearchUserItemResponse(**asdict(u)) for u in result.mutual_circle],
        popular_authors=[SearchUserItemResponse(**asdict(u)) for u in result.popular_authors],
        random_with_cards=[SearchUserItemResponse(**asdict(u)) for u in result.random_with_cards],
    )
