from __future__ import annotations

import datetime as dt
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from api.watchlist.schemas import (
    WatchlistEntryCreate,
    WatchlistEntryResponse,
    WatchlistEntryUpdate,
)
from core.database import get_db
from deps.auth import CurrentUser
from models.watchlist_entry import WatchlistEntry
from services.watchlist.create_watchlist_entry import CreateWatchlistEntryService

router = APIRouter(prefix='/watchlist', tags=['watchlist'])


def _entry_response(entry: WatchlistEntry) -> WatchlistEntryResponse:
    stored_ids = entry.watch_with_user_ids or []
    partner_ids = [UUID(str(raw)) for raw in stored_ids]
    return WatchlistEntryResponse(
        id=entry.id,
        user_id=entry.user_id,
        card_id=entry.card_id,
        provider_meta=entry.provider_meta,
        watch_tag=entry.watch_tag,
        watch_with_user_id=entry.watch_with_user_id,
        watch_with_user_ids=partner_ids,
    )


@router.post('', response_model=WatchlistEntryResponse, status_code=status.HTTP_201_CREATED)
async def create_watchlist_entry(
    body: WatchlistEntryCreate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> WatchlistEntryResponse:
    service = CreateWatchlistEntryService.build(db)
    try:
        result = await service.execute(
            actor_user_id=user.id,
            card_id=body.card_id,
            provider_meta=body.provider_meta,
            watch_tag=body.watch_tag.value,
            company=body.company,
            category_id=body.category_id,
            watch_note=body.watch_note,
            watch_with_user_id=body.watch_with_user_id,
            watch_with_user_ids=body.watch_with_user_ids,
            created_at=dt.datetime.now(dt.UTC),
        )
    except CreateWatchlistEntryService.WatchlistEntryAlreadyExistsError:
        raise HTTPException(status_code=409, detail='watchlist entry already exists') from None
    return _entry_response(result.actor_entry)


@router.patch('/{entry_id}', response_model=WatchlistEntryResponse)
async def update_watchlist_entry(
    entry_id: int,
    body: WatchlistEntryUpdate,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> WatchlistEntryResponse:
    entry = await db.get(WatchlistEntry, entry_id)
    if entry is None:
        raise HTTPException(status_code=404, detail='not_found')
    if entry.user_id != user.id:
        raise HTTPException(status_code=403, detail='forbidden')
    entry.watch_tag = body.watch_tag.value
    await db.commit()
    await db.refresh(entry)
    return _entry_response(entry)
