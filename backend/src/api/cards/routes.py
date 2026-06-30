from __future__ import annotations

import asyncio
from typing import Annotated
from uuid import UUID

import httpx
import orjson
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.cards.feed_post_feed_mapping import (
    feed_post_feed_item_to_response,
    inline_mention_snippets_to_response,
    inline_user_card_snippets_to_response,
)
from api.cards.schemas import (
    CardCreateRequest,
    CardResponse,
    CardUpdateRequest,
    FeedPostFeedItemResponse,
    FollowingRatingEntryResponse,
    FollowingRatingsListResponse,
    ShareCardRequest,
    ShareCardResponse,
    UserCardAudioTelegramResponse,
    UserCardCategorySnippet,
    UserCardCommentAuthorResponse,
    UserCardCommentCreateRequest,
    UserCardCommentListResponse,
    UserCardCommentResponse,
    UserCardDetailResponse,
    UserCardFeedItemResponse,
    UserCardFeedPageResponse,
    WatchedInlinePickerListResponse,
    WatchedInlinePickerRowResponse,
)
from api.feed_posts.schemas import FeedPostImageUploadResponse
from api.reactions.schemas import reaction_target_summary_to_response
from celery_app import app as celery_application
from conf import settings
from const.feed import FeedMode
from core.database import get_db
from core.rustfs_s3_client import (
    RustfsClientError,
    RustfsKeyNotFoundError,
    get_rustfs_object_bytes,
)
from deps.auth import CurrentUser
from models.card_comment import CardComment
from models.card_tag import CardTag
from models.user import User
from models.user_card import UserCard
from models.user_card_category import UserCardCategory
from services.cards.attach_user_card_audio import (
    AttachUserCardAudioService,
)
from services.cards.attach_user_card_audio import (
    UserCardForbiddenError as AttachCardAudioForbiddenError,
)
from services.cards.attach_user_card_audio import (
    UserCardNotFoundError as AttachCardAudioNotFoundError,
)
from services.cards.create_user_card import (
    CatalogItemNotFoundError,
    CreateUserCardInput,
    CreateUserCardService,
    FilmNotFoundError,
    UserCardAlreadyExistsError,
    UserCardValidationError,
)
from services.cards.create_user_card_comment import (
    CreateUserCardCommentInput,
    CreateUserCardCommentService,
    ParentCommentMismatchError,
    ParentCommentNotFoundError,
    UserCardCommentValidationError,
)
from services.cards.create_user_card_comment import (
    UserCardNotFoundError as CommentCreateUserCardNotFoundError,
)
from services.cards.delete_user_card import DeleteUserCardService
from services.cards.delete_user_card import (
    UserCardForbiddenError as DeleteUserCardForbiddenError,
)
from services.cards.delete_user_card import (
    UserCardNotFoundError as DeleteUserCardNotFoundError,
)
from services.cards.delete_user_card_audio import DeleteUserCardAudioService
from services.cards.delete_user_card_audio import (
    UserCardForbiddenError as DeleteCardAudioForbiddenError,
)
from services.cards.delete_user_card_audio import (
    UserCardNotFoundError as DeleteCardAudioNotFoundError,
)
from services.cards.get_user_card_details import GetUserCardDetailsService, UserCardNotFoundError
from services.cards.inline_user_card_ref_tokens import batch_resolve_inline_user_card_refs
from services.cards.list_following_ratings_for_user_card import (
    FollowingRatingRow,
    ListFollowingRatingsForUserCardService,
    UserCardAnchorNotFoundError,
)
from services.cards.list_my_user_cards_for_inline_picker import (
    ListMyUserCardsForInlinePickerService,
)
from services.cards.list_user_card_comments import (
    CommentNotFoundError,
    ListUserCardCommentsService,
    UserCardCommentItem,
)
from services.cards.list_user_card_comments import (
    UserCardNotFoundError as ListCommentsUserCardNotFoundError,
)
from services.cards.list_user_card_feed import (
    FeedPostFeedItem,
    ListUserCardFeedService,
)
from services.cards.send_user_card_audio_to_telegram import (
    SendUserCardAudioToTelegramService,
    UserCardAudioFetchError,
    UserCardAudioKeyInvalidError,
    UserCardAudioMissingError,
    UserCardAudioObjectNotFoundError,
    UserCardAudioStorageNotConfiguredError,
    UserCardAudioTooLargeError,
)
from services.cards.share_user_card import (
    ShareRecipientsEmptyError,
    ShareRecipientsNotFollowersError,
    ShareRecipientsTooManyError,
    ShareUserCardForbiddenError,
    ShareUserCardService,
    UserCardNotFoundForShareError,
)
from services.cards.update_user_card import (
    UpdateUserCardInput,
    UpdateUserCardService,
)
from services.cards.update_user_card import (
    UserCardForbiddenError as UpdateUserCardForbiddenError,
)
from services.cards.update_user_card import (
    UserCardNotFoundError as UpdateUserCardNotFoundError,
)
from services.cards.update_user_card import (
    UserCardValidationError as UpdateUserCardValidationError,
)
from services.cards.upload_user_card_audio import (
    USER_CARD_AUDIO_MAX_BYTES,
    UserCardAudioUploadError,
)
from services.feed.global_feed_head_broker import bump_global_feed_head_version
from services.feed_posts import (
    FEED_POST_IMAGE_MAX_BYTES,
    FeedPostImageUploadError,
    UploadFeedPostImageService,
)
from services.profile.batch_resolve_inline_mentions import batch_resolve_inline_mentions
from services.reactions import GetReactionSummariesForTargetsService
from services.subscriptions.list_follower_user_ids_for_following_user import (
    ListFollowerUserIdsForFollowingUserService,
)
from services.telegram.send_bot_message import SendTelegramBotMessageService
from utils.user_card_media_key import is_safe_user_card_media_key

router = APIRouter(prefix='/cards', tags=['cards'])


async def _card_response_from_user_card(
    db: AsyncSession, card: UserCard, tags: list[str]
) -> CardResponse:
    title = (card.display_title or '').strip() or 'Untitled'
    cat = (
        await db.execute(select(UserCardCategory).where(UserCardCategory.id == card.category_id))
    ).scalar_one_or_none()
    if cat is None:
        raise RuntimeError('card category missing')
    return CardResponse(
        id=card.id,
        film_id=card.film_id,
        catalog_item_id=card.catalog_item_id,
        provider=card.provider,
        external_id=card.external_id,
        display_title=title,
        rating=float(card.rating),
        company=card.company,
        mood_before=card.mood_before,
        mood_after=card.mood_after,
        custom_tags=list(tags),
        category=UserCardCategorySnippet(id=cat.id, name=cat.name),
        is_favorite=bool(card.is_favorite),
        audio_url=card.audio_url,
    )


async def _read_upload_body_max(file: UploadFile, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = await file.read(64 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(status_code=413, detail='file too large') from None
        chunks.append(chunk)
    return b''.join(chunks)


@router.get(
    '/media/{media_key:path}',
    summary='Аудио карточки из RustFS (без Bearer для audio src / скачивания)',
)
async def get_user_card_media(media_key: str) -> Response:
    if not is_safe_user_card_media_key(media_key):
        raise HTTPException(status_code=404, detail='not found') from None
    internal = settings.reaction_media.rustfs_internal_base_url.strip().rstrip('/')
    if not internal:
        raise HTTPException(status_code=503, detail='media proxy not configured') from None
    bucket = settings.reaction_media.rustfs_bucket.strip()
    safe_key = media_key.lstrip('/')
    access = settings.reaction_media.rustfs_access_key.strip()
    secret = settings.reaction_media.rustfs_secret_key.strip()
    headers: dict[str, str] = {'Cache-Control': 'public, max-age=86400'}

    if access and secret:
        try:
            result = await asyncio.to_thread(
                get_rustfs_object_bytes,
                endpoint_url=internal,
                access_key_id=access,
                secret_access_key=secret,
                bucket=bucket,
                key=safe_key,
            )
        except RustfsKeyNotFoundError:
            raise HTTPException(status_code=404, detail='not found') from None
        except RustfsClientError:
            raise HTTPException(status_code=502, detail='storage unreachable') from None
        media = (
            result.content_type.strip()
            if isinstance(result.content_type, str) and result.content_type.strip()
            else 'application/octet-stream'
        )
        return Response(content=result.body, media_type=media, headers=headers)

    url = f'{internal}/{bucket}/{safe_key}'
    timeout = httpx.Timeout(18.0)
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            upstream = await client.get(url)
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail='storage unreachable') from exc
    if upstream.status_code != 200:
        raise HTTPException(status_code=404, detail='not found') from None
    ct = upstream.headers.get('content-type')
    media = ct.strip() if isinstance(ct, str) and ct.strip() else 'application/octet-stream'
    return Response(content=upstream.content, media_type=media, headers=headers)


@router.post(
    '/comment-images/upload',
    response_model=FeedPostImageUploadResponse,
    summary='Загрузить изображение к комментарию карточки фильма',
)
async def upload_user_card_comment_image(
    user: CurrentUser,
    file: UploadFile = File(...),
) -> FeedPostImageUploadResponse:
    content_type = (file.content_type or '').strip()
    try:
        data = await _read_upload_body_max(file, FEED_POST_IMAGE_MAX_BYTES)
        url = await UploadFeedPostImageService.build().execute(
            user_id=user.id,
            content_type=content_type,
            data=data,
            media_subdir='movie_card_comments',
        )
    except HTTPException:
        raise
    except FeedPostImageUploadError as e:
        msg = str(e).lower()
        if 'not configured' in msg:
            raise HTTPException(status_code=503, detail=str(e)) from e
        raise HTTPException(status_code=400, detail=str(e)) from e
    return FeedPostImageUploadResponse(url=url)


@router.get(
    '/watched-inline-picker',
    response_model=WatchedInlinePickerListResponse,
    summary='Поиск своих карточек для вставки ⟦c{id}⟧ в комментарии и посты',
)
async def list_watched_inline_picker(
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    q: str = Query(default='', max_length=200),
    limit: int = Query(default=30, ge=1, le=80),
) -> WatchedInlinePickerListResponse:
    rows = await ListMyUserCardsForInlinePickerService.build(db).execute(
        user.id,
        query=q,
        limit=limit,
    )
    return WatchedInlinePickerListResponse(
        items=[
            WatchedInlinePickerRowResponse(
                movie_card_id=r.user_card_id,
                film_title=r.film_title,
                film_year=r.film_year,
            )
            for r in rows
        ]
    )


async def _load_comment_response(
    db: AsyncSession, comment_id: int, viewer_user_id: UUID
) -> UserCardCommentResponse:
    row = (
        await db.execute(
            select(CardComment, User)
            .join(User, User.id == CardComment.user_id)
            .where(CardComment.id == comment_id)
        )
    ).one()
    comment, author = row
    _, comment_rx, _, _ = await GetReactionSummariesForTargetsService(db).execute(
        viewer_user_id=viewer_user_id,
        user_card_ids=[],
        comment_ids=[comment.id],
        feed_post_comment_ids=[],
        feed_post_ids=[],
    )
    (snips,) = await batch_resolve_inline_user_card_refs(db, [(author.id, comment.text or '')])
    (mens,) = await batch_resolve_inline_mentions(db, [comment.text or ''])
    return UserCardCommentResponse(
        id=comment.id,
        movie_card_id=comment.card_id,
        parent_comment_id=comment.parent_comment_id,
        text=comment.text,
        image_url=comment.image_url,
        created_at=comment.created_at,
        replies_count=0,
        total_descendants_count=0,
        author=UserCardCommentAuthorResponse(
            id=author.id,
            profile_slug=author.profile_slug,
            username=author.username,
            first_name=author.first_name,
            last_name=author.last_name,
            photo_url=author.photo_url,
            display_name=author.display_name,
        ),
        reactions=reaction_target_summary_to_response(comment_rx[comment.id]),
        referenced_movie_cards=inline_user_card_snippets_to_response(snips),
        referenced_mentions=inline_mention_snippets_to_response(mens),
    )


def _comment_item_to_response(item: UserCardCommentItem) -> UserCardCommentResponse:
    return UserCardCommentResponse(
        id=item.id,
        movie_card_id=item.user_card_id,
        parent_comment_id=item.parent_comment_id,
        text=item.text,
        image_url=item.image_url,
        created_at=item.created_at,
        replies_count=item.replies_count,
        total_descendants_count=item.total_descendants_count,
        author=UserCardCommentAuthorResponse(
            id=item.author.id,
            profile_slug=item.author.profile_slug,
            username=item.author.username,
            first_name=item.author.first_name,
            last_name=item.author.last_name,
            photo_url=item.author.photo_url,
            display_name=item.author.display_name,
        ),
        reactions=reaction_target_summary_to_response(item.reactions),
        referenced_movie_cards=inline_user_card_snippets_to_response(
            item.referenced_inline_user_cards
        ),
        referenced_mentions=inline_mention_snippets_to_response(item.referenced_mentions),
    )


@router.post('', response_model=CardResponse, summary='Создать карточку фильма')
async def create_card(
    body: CardCreateRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CardResponse:
    try:
        card = await CreateUserCardService(db).execute(
            user.id,
            CreateUserCardInput(
                film_id=body.film_id,
                kinopoisk_id=body.kinopoisk_id,
                catalog_item_id=body.catalog_item_id,
                provider=body.provider,
                external_id=body.external_id,
                genres=body.genres,
                rating=body.rating,
                company=body.company,
                mood_before=body.mood_before,
                mood_after=body.mood_after,
                custom_tags=body.custom_tags,
                watch_note=body.watch_note,
                display_title=(body.display_title or '').strip() or None,
                display_cover_url=body.display_cover_url,
                display_summary=body.display_summary,
                category_id=body.category_id,
            ),
        )
    except FilmNotFoundError:
        raise HTTPException(status_code=404, detail='film not found') from None
    except CatalogItemNotFoundError:
        raise HTTPException(status_code=404, detail='catalog item not found') from None
    except UserCardAlreadyExistsError:
        raise HTTPException(status_code=409, detail='movie card already exists') from None
    except UserCardValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    tags = (
        (
            await db.execute(
                select(CardTag.tag).where(CardTag.card_id == card.id).order_by(CardTag.tag)
            )
        )
        .scalars()
        .all()
    )
    await bump_global_feed_head_version()
    follower_ids = await ListFollowerUserIdsForFollowingUserService.build(db).execute(user.id)
    if follower_ids:
        celery_application.tasks['tasks.telegram_engagement.notify_followers_new_user_card'].delay(
            actor_user_id=str(user.id),
            card_id=card.id,
            recipient_user_ids_json=orjson.dumps([str(x) for x in follower_ids]).decode(),
        )
    return await _card_response_from_user_card(db, card, list(tags))


@router.get('/feed', response_model=UserCardFeedPageResponse, summary='Лента карточек')
async def list_user_card_feed(
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    mode: FeedMode = Query(
        default='default',
        description='Смешанная лента, только подписки, или только подписчики (свои карточки фильмов скрыты; свои текстовые посты в ленте видны)',
    ),
) -> UserCardFeedPageResponse:
    page = await ListUserCardFeedService(db).execute(viewer.id, cursor, limit, feed_mode=mode)
    out_items: list[UserCardFeedItemResponse | FeedPostFeedItemResponse] = []
    for item in page.items:
        if isinstance(item, FeedPostFeedItem):
            out_items.append(feed_post_feed_item_to_response(item))
            continue
        out_items.append(
            UserCardFeedItemResponse(
                id=item.id,
                user_id=item.user_id,
                card_author=UserCardCommentAuthorResponse(
                    id=item.card_author.id,
                    profile_slug=item.card_author.profile_slug,
                    username=item.card_author.username,
                    first_name=item.card_author.first_name,
                    last_name=item.card_author.last_name,
                    photo_url=item.card_author.photo_url,
                    display_name=item.card_author.display_name,
                ),
                film_id=item.film_id,
                film_kinopoisk_id=item.film_kinopoisk_id,
                film_genres=item.film_genres,
                film_title=item.film_title,
                film_year=item.film_year,
                release_year=item.release_year,
                release_date=item.release_date,
                film_poster_url=item.film_poster_url,
                catalog_item_id=item.catalog_item_id,
                provider=item.provider,
                external_id=item.external_id,
                display_title=item.display_title,
                display_cover_url=item.display_cover_url,
                display_summary=item.display_summary,
                rating=item.rating,
                company=item.company,
                mood_before=item.mood_before,
                mood_after=item.mood_after,
                custom_tags=item.custom_tags,
                watch_note=item.watch_note,
                category=UserCardCategorySnippet(id=item.category_id, name=item.category_name),
                feed_source=item.feed_source,
                reactions=reaction_target_summary_to_response(item.reactions),
                comments_count=item.comments_count,
                comments_preview=[_comment_item_to_response(c) for c in item.comments_preview],
                is_favorite=item.is_favorite,
                is_planned=item.is_planned,
                audio_url=item.audio_url,
            )
        )
    return UserCardFeedPageResponse(items=out_items, next_cursor=page.next_cursor)


@router.get(
    '/{card_id}/following-ratings',
    response_model=FollowingRatingsListResponse,
    summary='Оценки того же фильма среди ваших подписок',
)
async def list_following_ratings_for_user_card(
    card_id: int,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FollowingRatingsListResponse:
    try:
        result = await ListFollowingRatingsForUserCardService(db).execute(viewer.id, card_id)
    except UserCardAnchorNotFoundError:
        raise HTTPException(status_code=404, detail='movie card not found') from None

    def _entry(r: FollowingRatingRow) -> FollowingRatingEntryResponse:
        return FollowingRatingEntryResponse(
            user_id=r.user_id,
            movie_card_id=r.user_card_id,
            profile_slug=r.profile_slug,
            username=r.username,
            first_name=r.first_name,
            last_name=r.last_name,
            photo_url=r.photo_url,
            display_name=r.display_name,
            rating=r.rating,
        )

    return FollowingRatingsListResponse(
        viewer_rating=_entry(result.viewer_row) if result.viewer_row is not None else None,
        items=[_entry(r) for r in result.items],
    )


@router.post(
    '/{card_id}/audio',
    response_model=FeedPostImageUploadResponse,
    summary='Загрузить или заменить аудио к карточке',
)
async def upload_user_card_audio(
    card_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    file: UploadFile = File(...),
) -> FeedPostImageUploadResponse:
    content_type = (file.content_type or '').strip()
    try:
        data = await _read_upload_body_max(file, USER_CARD_AUDIO_MAX_BYTES)
        card = await AttachUserCardAudioService.build(db).execute(
            card_id=card_id,
            viewer_user_id=user.id,
            content_type=content_type,
            data=data,
        )
    except HTTPException:
        raise
    except AttachCardAudioNotFoundError:
        raise HTTPException(status_code=404, detail='movie card not found') from None
    except AttachCardAudioForbiddenError:
        raise HTTPException(status_code=403, detail='forbidden') from None
    except UserCardAudioUploadError as e:
        msg = str(e).lower()
        if 'not configured' in msg:
            raise HTTPException(status_code=503, detail=str(e)) from e
        raise HTTPException(status_code=400, detail=str(e)) from e
    url = card.audio_url or ''
    return FeedPostImageUploadResponse(url=url)


@router.delete(
    '/{card_id}/audio',
    status_code=204,
    response_class=Response,
    summary='Удалить аудио с карточки',
)
async def delete_user_card_audio_route(
    card_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    try:
        await DeleteUserCardAudioService.build(db).execute(card_id=card_id, viewer_user_id=user.id)
    except DeleteCardAudioNotFoundError:
        raise HTTPException(status_code=404, detail='movie card not found') from None
    except DeleteCardAudioForbiddenError:
        raise HTTPException(status_code=403, detail='forbidden') from None
    return Response(status_code=204)


@router.post(
    '/{card_id}/audio/send-telegram',
    response_model=UserCardAudioTelegramResponse,
    summary='Отправить аудио с карточки в Telegram',
)
async def post_send_user_card_audio_to_telegram(
    card_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserCardAudioTelegramResponse:
    try:
        await SendUserCardAudioToTelegramService.build(db).execute(card_id=card_id, viewer=user)
    except UserCardNotFoundError:
        raise HTTPException(status_code=404, detail='movie card not found') from None
    except UserCardAudioMissingError:
        raise HTTPException(status_code=404, detail='no audio on this card') from None
    except UserCardAudioKeyInvalidError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except UserCardAudioStorageNotConfiguredError as e:
        raise HTTPException(status_code=503, detail=str(e)) from e
    except UserCardAudioObjectNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except UserCardAudioFetchError as e:
        raise HTTPException(status_code=502, detail=str(e)) from e
    except UserCardAudioTooLargeError as e:
        raise HTTPException(status_code=413, detail=str(e)) from e
    except SendTelegramBotMessageService.TelegramChatUnavailable:
        raise HTTPException(
            status_code=422,
            detail={
                'code': 'telegram_chat_unavailable',
                'message': (
                    'Чтобы получать уведомления, откройте бота в Telegram '
                    'и нажмите «Start» / «Запустить», затем попробуйте снова.'
                ),
                'bot_username': settings.telegram.bot_username,
            },
        ) from None
    except SendTelegramBotMessageService.TelegramDeliveryFailed as e:
        raise HTTPException(
            status_code=502,
            detail={
                'code': 'telegram_delivery_failed',
                'message': 'Не удалось связаться с Telegram. Попробуйте позже.',
            },
        ) from e

    return UserCardAudioTelegramResponse()


@router.get(
    '/{card_id}', response_model=UserCardDetailResponse, summary='Получить карточку фильма по id'
)
async def get_card(
    card_id: int,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserCardDetailResponse:
    try:
        card = await GetUserCardDetailsService(db).execute(card_id, viewer.id)
    except UserCardNotFoundError:
        raise HTTPException(status_code=404, detail='movie card not found') from None
    return UserCardDetailResponse(
        id=card.id,
        user_id=card.user_id,
        card_author=UserCardCommentAuthorResponse(
            id=card.card_author.id,
            profile_slug=card.card_author.profile_slug,
            username=card.card_author.username,
            first_name=card.card_author.first_name,
            last_name=card.card_author.last_name,
            photo_url=card.card_author.photo_url,
            display_name=card.card_author.display_name,
        ),
        film_id=card.film_id,
        film_kinopoisk_id=card.film_kinopoisk_id,
        film_genres=card.film_genres,
        film_title=card.film_title,
        film_year=card.film_year,
        release_year=card.release_year,
        release_date=card.release_date,
        film_poster_url=card.film_poster_url,
        catalog_item_id=card.catalog_item_id,
        provider=card.provider,
        external_id=card.external_id,
        display_title=card.display_title,
        display_cover_url=card.display_cover_url,
        display_summary=card.display_summary,
        film_short_description=card.film_short_description,
        film_description=card.film_description,
        rating=card.rating,
        company=card.company,
        mood_before=card.mood_before,
        mood_after=card.mood_after,
        custom_tags=card.custom_tags,
        watch_note=card.watch_note,
        category=UserCardCategorySnippet(id=card.category_id, name=card.category_name),
        reactions=reaction_target_summary_to_response(card.reactions),
        is_favorite=card.is_favorite,
        is_planned=card.is_planned,
        audio_url=card.audio_url,
        planned_watch_partners=[
            UserCardCommentAuthorResponse(
                id=partner.id,
                profile_slug=partner.profile_slug,
                username=partner.username,
                first_name=partner.first_name,
                last_name=partner.last_name,
                photo_url=partner.photo_url,
                display_name=partner.display_name,
            )
            for partner in card.planned_watch_partners
        ],
    )


@router.patch(
    '/{card_id}',
    response_model=CardResponse,
    summary='Обновить карточку фильма',
)
async def patch_card(
    card_id: int,
    body: CardUpdateRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CardResponse:
    try:
        card = await UpdateUserCardService(db).execute(
            card_id=card_id,
            viewer_user_id=user.id,
            payload=UpdateUserCardInput(
                rating=body.rating,
                company=body.company,
                mood_before=body.mood_before,
                mood_after=body.mood_after,
                custom_tags=body.custom_tags,
                watch_note=body.watch_note,
                is_favorite=body.is_favorite,
                category_id=body.category_id,
            ),
        )
    except UpdateUserCardNotFoundError:
        raise HTTPException(status_code=404, detail='movie card not found') from None
    except UpdateUserCardForbiddenError:
        raise HTTPException(status_code=403, detail='forbidden') from None
    except UpdateUserCardValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    tags = (
        (
            await db.execute(
                select(CardTag.tag).where(CardTag.card_id == card.id).order_by(CardTag.tag)
            )
        )
        .scalars()
        .all()
    )
    return await _card_response_from_user_card(db, card, list(tags))


@router.delete(
    '/{card_id}',
    status_code=204,
    response_class=Response,
    summary='Удалить карточку фильма',
)
async def delete_card(
    card_id: int,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> Response:
    try:
        await DeleteUserCardService(db).execute(card_id=card_id, viewer_user_id=user.id)
    except DeleteUserCardNotFoundError:
        raise HTTPException(status_code=404, detail='movie card not found') from None
    except DeleteUserCardForbiddenError:
        raise HTTPException(status_code=403, detail='forbidden') from None
    return Response(status_code=204)


@router.post(
    '/{card_id}/share',
    response_model=ShareCardResponse,
    summary='Отправить карточку подписчикам в Telegram',
)
async def share_user_card(
    card_id: int,
    body: ShareCardRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ShareCardResponse:
    try:
        outcome = await ShareUserCardService(db).execute(
            actor_user_id=user.id,
            card_id=card_id,
            recipient_user_ids=list(body.recipient_user_ids),
        )
    except UserCardNotFoundForShareError:
        raise HTTPException(status_code=404, detail='movie card not found') from None
    except ShareUserCardForbiddenError:
        raise HTTPException(status_code=403, detail='forbidden') from None
    except ShareRecipientsEmptyError:
        raise HTTPException(status_code=422, detail='recipients required') from None
    except ShareRecipientsTooManyError:
        raise HTTPException(status_code=422, detail='too many recipients') from None
    except ShareRecipientsNotFollowersError:
        raise HTTPException(
            status_code=422,
            detail='recipients must be your subscribers only',
        ) from None

    share_comment = (body.share_comment or '').strip()
    for rid in outcome.recipient_ids:
        celery_application.tasks['tasks.telegram_engagement.deliver_shared_movie_card'].delay(
            actor_user_id=str(user.id),
            card_id=card_id,
            recipient_user_id=str(rid),
            share_comment=share_comment,
        )

    return ShareCardResponse(queued=len(outcome.recipient_ids))


@router.get(
    '/{card_id}/comments',
    response_model=UserCardCommentListResponse,
    summary='Получить комментарии карточки',
)
async def list_card_comments(
    card_id: int,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: int | None = Query(default=None, ge=1),
    limit: int = Query(default=20, ge=1),
) -> UserCardCommentListResponse:
    try:
        page = await ListUserCardCommentsService(db).execute(
            viewer.id,
            card_id=card_id,
            parent_comment_id=None,
            cursor=cursor,
            limit=min(limit, 50),
            flat=True,
        )
    except ListCommentsUserCardNotFoundError:
        raise HTTPException(status_code=404, detail='movie card not found') from None
    return UserCardCommentListResponse(
        items=[_comment_item_to_response(item) for item in page.items],
        next_cursor=page.next_cursor,
    )


@router.get(
    '/{card_id}/comments/{comment_id}/replies',
    response_model=UserCardCommentListResponse,
    summary='Получить ответы на комментарий',
)
async def list_card_comment_replies(
    card_id: int,
    comment_id: int,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: int | None = Query(default=None, ge=1),
    limit: int = Query(default=20, ge=1),
) -> UserCardCommentListResponse:
    try:
        page = await ListUserCardCommentsService(db).execute(
            viewer.id,
            card_id=card_id,
            parent_comment_id=comment_id,
            cursor=cursor,
            limit=min(limit, 50),
        )
    except ListCommentsUserCardNotFoundError:
        raise HTTPException(status_code=404, detail='movie card not found') from None
    except CommentNotFoundError:
        raise HTTPException(status_code=404, detail='comment not found') from None
    return UserCardCommentListResponse(
        items=[_comment_item_to_response(item) for item in page.items],
        next_cursor=page.next_cursor,
    )


@router.post(
    '/{card_id}/comments',
    response_model=UserCardCommentResponse,
    summary='Создать комментарий карточки',
)
async def create_card_comment(
    card_id: int,
    body: UserCardCommentCreateRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> UserCardCommentResponse:
    try:
        outcome = await CreateUserCardCommentService(db).execute(
            card_id,
            user.id,
            CreateUserCardCommentInput(
                text=body.text,
                parent_comment_id=body.parent_comment_id,
                image_url=body.image_url,
            ),
        )
    except CommentCreateUserCardNotFoundError:
        raise HTTPException(status_code=404, detail='movie card not found') from None
    except ParentCommentNotFoundError:
        raise HTTPException(status_code=404, detail='parent comment not found') from None
    except ParentCommentMismatchError:
        raise HTTPException(
            status_code=422, detail='parent comment belongs to another card'
        ) from None
    except UserCardCommentValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    created = outcome.comment
    mention_recipients = list(outcome.mentioned_user_ids)
    if body.parent_comment_id is not None:
        parent_author_id = (
            await db.execute(
                select(CardComment.user_id).where(CardComment.id == body.parent_comment_id)
            )
        ).scalar_one_or_none()
        if parent_author_id is not None:
            mention_recipients = [uid for uid in mention_recipients if uid != parent_author_id]
    else:
        card_owner_id = (
            await db.execute(select(UserCard.user_id).where(UserCard.id == card_id))
        ).scalar_one_or_none()
        if card_owner_id is not None:
            mention_recipients = [uid for uid in mention_recipients if uid != card_owner_id]

    if body.parent_comment_id is None:
        celery_application.tasks['tasks.telegram_engagement.notify_movie_card_root_comment'].delay(
            actor_user_id=str(user.id),
            card_id=card_id,
            comment_text=created.text,
        )
    else:
        celery_application.tasks['tasks.telegram_engagement.notify_comment_reply'].delay(
            actor_user_id=str(user.id),
            card_id=card_id,
            parent_comment_id=body.parent_comment_id,
            reply_text=created.text,
        )

    if mention_recipients:
        celery_application.tasks[
            'tasks.telegram_engagement.notify_movie_card_comment_mentions'
        ].delay(
            actor_user_id=str(user.id),
            card_id=card_id,
            comment_id=created.id,
            recipient_user_ids_json=orjson.dumps([str(x) for x in mention_recipients]).decode(),
        )

    return await _load_comment_response(db, created.id, user.id)
