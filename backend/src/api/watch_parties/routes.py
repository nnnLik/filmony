from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from api.watch_parties.schemas import (
    ActivePartyConflictResponse,
    WatchPartyBridgeResponse,
    WatchPartyCreateRequest,
    WatchPartyCreateResponse,
    WatchPartyInviteRequest,
    WatchPartyKickRequest,
    WatchPartyMemberResponse,
    WatchPartyMessageCreateRequest,
    WatchPartyMessageResponse,
    WatchPartyPlaybackRequest,
    WatchPartySlugResolveResponse,
    WatchPartySnapshotResponse,
    WatchPartyTypingRequest,
    WatchPartyWatchingBatchRequest,
    WatchPartyWatchingBatchResponse,
    WatchPartyWatchingItemResponse,
)
from core.database import get_db
from deps.auth import CurrentUser
from services.watch_parties.batch_user_watching import BatchUserWatchingService
from services.watch_parties.bridge_watch_party_to_watch_session import (
    BridgeWatchPartyToWatchSessionService,
)
from services.watch_parties.create_watch_party import CreateWatchPartyService
from services.watch_parties.end_watch_party import EndWatchPartyService
from services.watch_parties.get_watch_party import GetWatchPartyService, WatchPartySnapshotDTO
from services.watch_parties.get_watch_party_by_slug import GetWatchPartyBySlugService
from services.watch_parties.invite_watch_party_members import InviteWatchPartyMembersService
from services.watch_parties.join_watch_party import JoinWatchPartyService
from services.watch_parties.kick_watch_party_member import KickWatchPartyMemberService
from services.watch_parties.leave_watch_party import LeaveWatchPartyService
from services.watch_parties.record_watch_party_heartbeat import (
    BuildWatchPartySnapshotPayloadService,
    RecordWatchPartyHeartbeatService,
)
from services.watch_parties.record_watch_party_typing import RecordWatchPartyTypingService
from services.watch_parties.update_watch_party_playback import UpdateWatchPartyPlaybackService
from services.watch_parties.watch_party_broker import iter_watch_party_sse
from services.watch_parties.watch_party_messages import (
    CreateWatchPartyMessageService,
    DeleteWatchPartyMessageService,
    ListWatchPartyMessagesService,
)

router = APIRouter(prefix='/watch-parties', tags=['watch-parties'])


def _snapshot_response(dto: WatchPartySnapshotDTO) -> WatchPartySnapshotResponse:
    return WatchPartySnapshotResponse(
        id=dto.id,
        invite_slug=dto.invite_slug,
        invite_url=dto.invite_url,
        status=dto.status,
        film_id=dto.film_id,
        film_title=dto.film_title,
        film_poster_url=dto.film_poster_url,
        playback_iframe_url=dto.playback_iframe_url,
        playback_expires_at=dto.playback_expires_at,
        playback_state=dto.playback_state,
        host_user_id=dto.host_user_id,
        members=[
            WatchPartyMemberResponse(
                user_id=member.user_id,
                display_name=member.display_name,
                photo_url=member.photo_url,
                role=member.role,
                status=member.status,
                joined_at=member.joined_at,
            )
            for member in dto.members
        ],
        viewer_role=dto.viewer_role,
        viewer_status=dto.viewer_status,
    )


def _raise_active_party_conflict(exc: CreateWatchPartyService.AlreadyInActiveParty) -> None:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail={
            'code': 'already_in_active_party',
            'active_party_id': str(exc.active_party_id),
            'invite_slug': exc.invite_slug,
        },
    ) from None


@router.post('', response_model=WatchPartyCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_watch_party(
    body: WatchPartyCreateRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> WatchPartyCreateResponse:
    service = CreateWatchPartyService.build(db)
    try:
        result = await service.execute(actor_user_id=user.id, film_id=body.film_id)
    except CreateWatchPartyService.AlreadyInActiveParty as exc:
        _raise_active_party_conflict(exc)
    except CreateWatchPartyService.FilmNotFound:
        raise HTTPException(status_code=404, detail='film_not_found') from None
    except CreateWatchPartyService.PlaybackUnavailable:
        raise HTTPException(status_code=422, detail='playback_unavailable') from None
    return WatchPartyCreateResponse(
        id=result.party_id,
        invite_slug=result.invite_slug,
        invite_url=result.invite_url,
    )


@router.post('/watching/batch', response_model=WatchPartyWatchingBatchResponse)
async def batch_user_watching(
    body: WatchPartyWatchingBatchRequest,
    user: CurrentUser,
) -> WatchPartyWatchingBatchResponse:
    _ = user
    items = await BatchUserWatchingService.build().execute(list(body.user_ids))
    return WatchPartyWatchingBatchResponse(
        items={
            str(user_id): WatchPartyWatchingItemResponse(
                film_id=item.film_id,
                film_title=item.film_title,
                party_id=item.party_id,
            )
            for user_id, item in items.items()
        },
    )


@router.get('/by-slug/{invite_slug}', response_model=WatchPartySlugResolveResponse)
async def get_watch_party_by_slug(
    invite_slug: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> WatchPartySlugResolveResponse:
    _ = user
    service = GetWatchPartyBySlugService.build(db)
    try:
        result = await service.execute(invite_slug=invite_slug)
    except GetWatchPartyBySlugService.PartyNotFound:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except GetWatchPartyBySlugService.PartyEnded:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    return WatchPartySlugResolveResponse(
        party_id=result.party_id,
        invite_slug=result.invite_slug,
        status=result.status,
    )


@router.get('/{party_id}', response_model=WatchPartySnapshotResponse)
async def get_watch_party(
    party_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> WatchPartySnapshotResponse:
    service = GetWatchPartyService.build(db)
    try:
        snapshot = await service.execute(party_id=party_id, viewer_user_id=user.id)
    except GetWatchPartyService.PartyNotFound:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except GetWatchPartyService.PartyEnded:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except GetWatchPartyService.NotMember:
        raise HTTPException(status_code=403, detail='not_member') from None
    return _snapshot_response(snapshot)


@router.post('/{party_id}/join', status_code=status.HTTP_204_NO_CONTENT)
async def join_watch_party(
    party_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    service = JoinWatchPartyService.build(db)
    try:
        await service.execute(party_id=party_id, actor_user_id=user.id)
    except JoinWatchPartyService.PartyNotFound:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except JoinWatchPartyService.PartyEnded:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except JoinWatchPartyService.AlreadyInActiveParty as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                'code': 'already_in_active_party',
                'active_party_id': str(exc.active_party_id),
                'invite_slug': exc.invite_slug,
            },
        ) from None
    except JoinWatchPartyService.PartyFull:
        raise HTTPException(status_code=409, detail='party_full') from None
    except JoinWatchPartyService.PlaybackUnavailable:
        raise HTTPException(status_code=422, detail='playback_unavailable') from None


@router.post('/{party_id}/leave', status_code=status.HTTP_204_NO_CONTENT)
async def leave_watch_party(
    party_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    service = LeaveWatchPartyService.build(db)
    try:
        await service.execute(party_id=party_id, actor_user_id=user.id)
    except LeaveWatchPartyService.PartyNotFound:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except LeaveWatchPartyService.PartyEnded:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except LeaveWatchPartyService.NotMember:
        raise HTTPException(status_code=403, detail='not_member') from None


@router.post('/{party_id}/end', status_code=status.HTTP_204_NO_CONTENT)
async def end_watch_party(
    party_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    service = EndWatchPartyService.build(db)
    try:
        await service.execute(party_id=party_id, actor_user_id=user.id)
    except EndWatchPartyService.PartyNotFound:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except EndWatchPartyService.PartyEnded:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except EndWatchPartyService.HostRequired:
        raise HTTPException(status_code=403, detail='host_required') from None


@router.post('/{party_id}/kick', status_code=status.HTTP_204_NO_CONTENT)
async def kick_watch_party_member(
    party_id: UUID,
    body: WatchPartyKickRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    service = KickWatchPartyMemberService.build(db)
    try:
        await service.execute(
            party_id=party_id,
            actor_user_id=user.id,
            target_user_id=body.user_id,
        )
    except KickWatchPartyMemberService.PartyNotFound:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except KickWatchPartyMemberService.PartyEnded:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except KickWatchPartyMemberService.HostRequired:
        raise HTTPException(status_code=403, detail='host_required') from None
    except KickWatchPartyMemberService.TargetNotFound:
        raise HTTPException(status_code=404, detail='member_not_found') from None
    except KickWatchPartyMemberService.CannotKickHost:
        raise HTTPException(status_code=422, detail='cannot_kick_host') from None


@router.post('/{party_id}/playback')
async def update_watch_party_playback(
    party_id: UUID,
    body: WatchPartyPlaybackRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    service = UpdateWatchPartyPlaybackService.build(db)
    try:
        return await service.execute(
            party_id=party_id,
            actor_user_id=user.id,
            action=body.action,
            position_ms=body.position_ms,
        )
    except UpdateWatchPartyPlaybackService.PartyNotFound:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except UpdateWatchPartyPlaybackService.PartyEnded:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except UpdateWatchPartyPlaybackService.HostRequired:
        raise HTTPException(status_code=403, detail='host_required') from None
    except UpdateWatchPartyPlaybackService.InvalidAction:
        raise HTTPException(status_code=422, detail='invalid_playback_action') from None
    except UpdateWatchPartyPlaybackService.SeekRateLimited:
        raise HTTPException(status_code=429, detail='seek_rate_limited') from None


@router.get('/{party_id}/messages', response_model=list[WatchPartyMessageResponse])
async def list_watch_party_messages(
    party_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    cursor: int | None = Query(default=None, ge=1),
    limit: int = Query(default=50, ge=1, le=50),
) -> list[WatchPartyMessageResponse]:
    service = ListWatchPartyMessagesService.build(db)
    try:
        messages = await service.execute(
            party_id=party_id,
            actor_user_id=user.id,
            cursor=cursor,
            limit=limit,
        )
    except ListWatchPartyMessagesService.PartyNotFound:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except ListWatchPartyMessagesService.PartyEnded:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except ListWatchPartyMessagesService.NotMember:
        raise HTTPException(status_code=403, detail='not_member') from None
    return [
        WatchPartyMessageResponse(
            id=message.id,
            author_user_id=message.author_user_id,
            body=message.body,
            created_at=message.created_at,
        )
        for message in messages
    ]


@router.post('/{party_id}/messages', response_model=WatchPartyMessageResponse, status_code=201)
async def create_watch_party_message(
    party_id: UUID,
    body: WatchPartyMessageCreateRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> WatchPartyMessageResponse:
    service = CreateWatchPartyMessageService.build(db)
    try:
        message = await service.execute(
            party_id=party_id,
            actor_user_id=user.id,
            body=body.body,
        )
    except CreateWatchPartyMessageService.PartyNotFound:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except CreateWatchPartyMessageService.PartyEnded:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except CreateWatchPartyMessageService.NotMember:
        raise HTTPException(status_code=403, detail='not_member') from None
    except CreateWatchPartyMessageService.BodyTooLong:
        raise HTTPException(status_code=422, detail='message_too_long') from None
    except CreateWatchPartyMessageService.RateLimited:
        raise HTTPException(status_code=429, detail='message_rate_limited') from None
    return WatchPartyMessageResponse(
        id=message.id,
        author_user_id=message.author_user_id,
        body=message.body,
        created_at=message.created_at,
    )


@router.delete('/{party_id}/messages/{message_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_watch_party_message(
    party_id: UUID,
    message_id: int,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    service = DeleteWatchPartyMessageService.build(db)
    try:
        await service.execute(
            party_id=party_id,
            actor_user_id=user.id,
            message_id=message_id,
        )
    except DeleteWatchPartyMessageService.PartyNotFound:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except DeleteWatchPartyMessageService.PartyEnded:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except DeleteWatchPartyMessageService.NotMember:
        raise HTTPException(status_code=403, detail='not_member') from None
    except DeleteWatchPartyMessageService.MessageNotFound:
        raise HTTPException(status_code=404, detail='message_not_found') from None
    except DeleteWatchPartyMessageService.Forbidden:
        raise HTTPException(status_code=403, detail='forbidden') from None


@router.post('/{party_id}/typing', status_code=status.HTTP_204_NO_CONTENT)
async def watch_party_typing(
    party_id: UUID,
    body: WatchPartyTypingRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    service = RecordWatchPartyTypingService.build(db)
    try:
        await service.execute(
            party_id=party_id,
            actor_user_id=user.id,
            display_name=body.display_name,
        )
    except RecordWatchPartyTypingService.PartyNotFound:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except RecordWatchPartyTypingService.PartyEnded:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except RecordWatchPartyTypingService.NotMember:
        raise HTTPException(status_code=403, detail='not_member') from None
    except RecordWatchPartyTypingService.RateLimited:
        raise HTTPException(status_code=429, detail='typing_rate_limited') from None


@router.post('/{party_id}/invite', status_code=status.HTTP_204_NO_CONTENT)
async def invite_watch_party_members(
    party_id: UUID,
    body: WatchPartyInviteRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    service = InviteWatchPartyMembersService.build(db)
    try:
        await service.execute(
            party_id=party_id,
            actor_user_id=user.id,
            user_ids=body.user_ids,
        )
    except InviteWatchPartyMembersService.PartyNotFound:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except InviteWatchPartyMembersService.PartyEnded:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except InviteWatchPartyMembersService.HostRequired:
        raise HTTPException(status_code=403, detail='host_required') from None
    except InviteWatchPartyMembersService.PartyFull:
        raise HTTPException(status_code=409, detail='party_full') from None
    except InviteWatchPartyMembersService.InvalidTarget:
        raise HTTPException(status_code=422, detail='invalid_invite_target') from None


@router.post('/{party_id}/bridge-watch-session', response_model=WatchPartyBridgeResponse)
async def bridge_watch_party_to_watch_session(
    party_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> WatchPartyBridgeResponse:
    service = BridgeWatchPartyToWatchSessionService.build(db)
    try:
        result = await service.execute(party_id=party_id, actor_user_id=user.id)
    except BridgeWatchPartyToWatchSessionService.PartyNotFound:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except BridgeWatchPartyToWatchSessionService.PartyEnded:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except BridgeWatchPartyToWatchSessionService.HostRequired:
        raise HTTPException(status_code=403, detail='host_required') from None
    except BridgeWatchPartyToWatchSessionService.InvalidRoster:
        raise HTTPException(status_code=422, detail='invalid_roster') from None
    return WatchPartyBridgeResponse(watch_session_id=result.watch_session_id)


@router.post('/{party_id}/heartbeat', status_code=status.HTTP_204_NO_CONTENT)
async def watch_party_heartbeat(
    party_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> None:
    service = RecordWatchPartyHeartbeatService.build(db)
    try:
        await service.execute(party_id=party_id, actor_user_id=user.id)
    except RecordWatchPartyHeartbeatService.PartyNotFound:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except RecordWatchPartyHeartbeatService.PartyEnded:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except RecordWatchPartyHeartbeatService.NotMember:
        raise HTTPException(status_code=403, detail='not_member') from None


@router.get('/{party_id}/events')
async def watch_party_events(
    party_id: UUID,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    since_seq: int | None = Query(default=None, ge=0),
) -> StreamingResponse:
    snapshot_service = BuildWatchPartySnapshotPayloadService.build(db)
    member_check = GetWatchPartyService.build(db)
    try:
        await member_check.execute(
            party_id=party_id,
            viewer_user_id=user.id,
            require_membership=True,
        )
        snapshot = await snapshot_service.execute(party_id=party_id)
    except GetWatchPartyService.PartyNotFound:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except GetWatchPartyService.PartyEnded:
        raise HTTPException(status_code=404, detail='party_not_found') from None
    except GetWatchPartyService.NotMember:
        raise HTTPException(status_code=403, detail='not_member') from None

    async def gen():
        async for chunk in iter_watch_party_sse(
            party_id,
            snapshot_payload=snapshot,
            since_seq=since_seq,
        ):
            yield chunk

    return StreamingResponse(
        gen(),
        media_type='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no',
        },
    )
