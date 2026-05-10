from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from api.cards.schemas import (
    CardCreateRequest,
    CardDetailResponse,
    CardResponse,
    CardUpdateRequest,
    FollowingRatingEntryResponse,
    FollowingRatingsListResponse,
    MovieCardCommentAuthorResponse,
    MovieCardCommentCreateRequest,
    MovieCardCommentListResponse,
    MovieCardCommentResponse,
    MovieCardFeedItemResponse,
    MovieCardFeedPageResponse,
    ShareCardRequest,
    ShareCardResponse,
)
from api.reactions.schemas import reaction_target_summary_to_response
from celery_app import app as celery_application
from const.feed import FeedMode
from core.database import get_db
from deps.auth import CurrentUser
from models.movie_card_comment import MovieCardComment
from models.movie_card_tag import MovieCardTag
from models.user import User
from services.cards.create_movie_card import (
    CreateMovieCardInput,
    CreateMovieCardService,
    FilmNotFoundError,
    MovieCardAlreadyExistsError,
    MovieCardValidationError,
)
from services.cards.create_movie_card_comment import (
    CreateMovieCardCommentInput,
    CreateMovieCardCommentService,
    MovieCardCommentValidationError,
    ParentCommentMismatchError,
    ParentCommentNotFoundError,
)
from services.cards.create_movie_card_comment import (
    MovieCardNotFoundError as CommentMovieCardNotFoundError,
)
from services.cards.delete_movie_card import DeleteMovieCardService
from services.cards.delete_movie_card import (
    MovieCardForbiddenError as DeleteMovieCardForbiddenError,
)
from services.cards.delete_movie_card import (
    MovieCardNotFoundError as DeleteMovieCardNotFoundError,
)
from services.cards.get_movie_card_details import GetMovieCardDetailsService, MovieCardNotFoundError
from services.cards.list_following_ratings_for_movie_card import (
    ListFollowingRatingsForMovieCardService,
    MovieCardAnchorNotFoundError,
)
from services.cards.list_movie_card_comments import (
    CommentNotFoundError,
    ListMovieCardCommentsService,
    MovieCardCommentItem,
)
from services.cards.list_movie_card_comments import (
    MovieCardNotFoundError as ListCommentsMovieCardNotFoundError,
)
from services.cards.list_movie_card_feed import ListMovieCardFeedService
from services.cards.share_movie_card import (
    MovieCardNotFoundForShareError,
    ShareMovieCardForbiddenError,
    ShareMovieCardService,
    ShareRecipientsEmptyError,
    ShareRecipientsNotFollowersError,
    ShareRecipientsTooManyError,
)
from services.cards.update_movie_card import (
    MovieCardForbiddenError as UpdateMovieCardForbiddenError,
)
from services.cards.update_movie_card import (
    MovieCardNotFoundError as UpdateMovieCardNotFoundError,
)
from services.cards.update_movie_card import (
    MovieCardValidationError as UpdateMovieCardValidationError,
)
from services.cards.update_movie_card import (
    UpdateMovieCardInput,
    UpdateMovieCardService,
)
from services.reactions import GetReactionSummariesForTargetsService

router = APIRouter(prefix='/cards', tags=['cards'])


async def _load_comment_response(
    db: AsyncSession, comment_id: int, viewer_user_id: UUID
) -> MovieCardCommentResponse:
    row = (
        await db.execute(
            select(MovieCardComment, User)
            .join(User, User.id == MovieCardComment.user_id)
            .where(MovieCardComment.id == comment_id)
        )
    ).one()
    comment, author = row
    _, comment_rx = await GetReactionSummariesForTargetsService(db).execute(
        viewer_user_id=viewer_user_id,
        movie_card_ids=[],
        comment_ids=[comment.id],
    )
    return MovieCardCommentResponse(
        id=comment.id,
        movie_card_id=comment.movie_card_id,
        parent_comment_id=comment.parent_comment_id,
        text=comment.text,
        created_at=comment.created_at,
        replies_count=0,
        total_descendants_count=0,
        author=MovieCardCommentAuthorResponse(
            id=author.id,
            profile_slug=author.profile_slug,
            username=author.username,
            first_name=author.first_name,
            last_name=author.last_name,
            photo_url=author.photo_url,
            display_name=author.display_name,
        ),
        reactions=reaction_target_summary_to_response(comment_rx[comment.id]),
    )


def _comment_item_to_response(item: MovieCardCommentItem) -> MovieCardCommentResponse:
    return MovieCardCommentResponse(
        id=item.id,
        movie_card_id=item.movie_card_id,
        parent_comment_id=item.parent_comment_id,
        text=item.text,
        created_at=item.created_at,
        replies_count=item.replies_count,
        total_descendants_count=item.total_descendants_count,
        author=MovieCardCommentAuthorResponse(
            id=item.author.id,
            profile_slug=item.author.profile_slug,
            username=item.author.username,
            first_name=item.author.first_name,
            last_name=item.author.last_name,
            photo_url=item.author.photo_url,
            display_name=item.author.display_name,
        ),
        reactions=reaction_target_summary_to_response(item.reactions),
    )


@router.post('', response_model=CardResponse, summary='Создать карточку фильма')
async def create_card(
    body: CardCreateRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CardResponse:
    try:
        card = await CreateMovieCardService(db).execute(
            user.id,
            CreateMovieCardInput(
                film_id=body.film_id,
                kinopoisk_id=body.kinopoisk_id,
                genres=body.genres,
                rating=body.rating,
                company=body.company,
                mood_before=body.mood_before,
                mood_after=body.mood_after,
                custom_tags=body.custom_tags,
            ),
        )
    except FilmNotFoundError:
        raise HTTPException(status_code=404, detail='film not found') from None
    except MovieCardAlreadyExistsError:
        raise HTTPException(status_code=409, detail='movie card already exists') from None
    except MovieCardValidationError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e

    tags = (
        (
            await db.execute(
                select(MovieCardTag.tag)
                .where(MovieCardTag.movie_card_id == card.id)
                .order_by(MovieCardTag.tag)
            )
        )
        .scalars()
        .all()
    )
    return CardResponse(
        id=card.id,
        film_id=card.film_id,
        rating=float(card.rating),
        company=card.company,
        mood_before=card.mood_before,
        mood_after=card.mood_after,
        custom_tags=list(tags),
        is_favorite=bool(card.is_favorite),
    )


@router.get('/feed', response_model=MovieCardFeedPageResponse, summary='Лента карточек')
async def list_movie_card_feed(
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: str | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=50),
    mode: FeedMode = Query(
        default='default',
        description='Смешанная лента, только подписки (и свои карточки), или только подписчики (и свои)',
    ),
    hide_own: bool = Query(
        default=False,
        description='Исключить свои карточки из персональных потоков (поток own обнуляется)',
    ),
) -> MovieCardFeedPageResponse:
    page = await ListMovieCardFeedService(db).execute(
        viewer.id, cursor, limit, feed_mode=mode, hide_own_cards=hide_own
    )
    return MovieCardFeedPageResponse(
        items=[
            MovieCardFeedItemResponse(
                id=item.id,
                user_id=item.user_id,
                film_id=item.film_id,
                film_kinopoisk_id=item.film_kinopoisk_id,
                film_genres=item.film_genres,
                film_title=item.film_title,
                film_year=item.film_year,
                film_poster_url=item.film_poster_url,
                rating=item.rating,
                company=item.company,
                mood_before=item.mood_before,
                mood_after=item.mood_after,
                custom_tags=item.custom_tags,
                feed_source=item.feed_source,
                reactions=reaction_target_summary_to_response(item.reactions),
                comments_count=item.comments_count,
                card_author=MovieCardCommentAuthorResponse(
                    id=item.card_author.id,
                    profile_slug=item.card_author.profile_slug,
                    username=item.card_author.username,
                    first_name=item.card_author.first_name,
                    last_name=item.card_author.last_name,
                    photo_url=item.card_author.photo_url,
                    display_name=item.card_author.display_name,
                ),
                comments_preview=[_comment_item_to_response(c) for c in item.comments_preview],
                is_favorite=item.is_favorite,
            )
            for item in page.items
        ],
        next_cursor=page.next_cursor,
    )


@router.get(
    '/{card_id}/following-ratings',
    response_model=FollowingRatingsListResponse,
    summary='Оценки того же фильма среди ваших подписок',
)
async def list_following_ratings_for_movie_card(
    card_id: int,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> FollowingRatingsListResponse:
    try:
        rows = await ListFollowingRatingsForMovieCardService(db).execute(viewer.id, card_id)
    except MovieCardAnchorNotFoundError:
        raise HTTPException(status_code=404, detail='movie card not found') from None
    return FollowingRatingsListResponse(
        items=[
            FollowingRatingEntryResponse(
                user_id=r.user_id,
                profile_slug=r.profile_slug,
                username=r.username,
                first_name=r.first_name,
                last_name=r.last_name,
                photo_url=r.photo_url,
                display_name=r.display_name,
                rating=r.rating,
            )
            for r in rows
        ],
    )


@router.get(
    '/{card_id}', response_model=CardDetailResponse, summary='Получить карточку фильма по id'
)
async def get_card(
    card_id: int,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> CardDetailResponse:
    try:
        card = await GetMovieCardDetailsService(db).execute(card_id, viewer.id)
    except MovieCardNotFoundError:
        raise HTTPException(status_code=404, detail='movie card not found') from None
    return CardDetailResponse(
        id=card.id,
        user_id=card.user_id,
        film_id=card.film_id,
        film_kinopoisk_id=card.film_kinopoisk_id,
        film_genres=card.film_genres,
        film_title=card.film_title,
        film_year=card.film_year,
        film_poster_url=card.film_poster_url,
        rating=card.rating,
        company=card.company,
        mood_before=card.mood_before,
        mood_after=card.mood_after,
        custom_tags=card.custom_tags,
        reactions=reaction_target_summary_to_response(card.reactions),
        is_favorite=card.is_favorite,
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
        card = await UpdateMovieCardService(db).execute(
            card_id=card_id,
            viewer_user_id=user.id,
            payload=UpdateMovieCardInput(
                rating=body.rating,
                company=body.company,
                mood_before=body.mood_before,
                mood_after=body.mood_after,
                custom_tags=body.custom_tags,
                is_favorite=body.is_favorite,
            ),
        )
    except UpdateMovieCardNotFoundError:
        raise HTTPException(status_code=404, detail='movie card not found') from None
    except UpdateMovieCardForbiddenError:
        raise HTTPException(status_code=403, detail='forbidden') from None
    except UpdateMovieCardValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    tags = (
        (
            await db.execute(
                select(MovieCardTag.tag)
                .where(MovieCardTag.movie_card_id == card.id)
                .order_by(MovieCardTag.tag)
            )
        )
        .scalars()
        .all()
    )
    return CardResponse(
        id=card.id,
        film_id=card.film_id,
        rating=float(card.rating),
        company=card.company,
        mood_before=card.mood_before,
        mood_after=card.mood_after,
        custom_tags=list(tags),
        is_favorite=bool(card.is_favorite),
    )


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
        await DeleteMovieCardService(db).execute(card_id=card_id, viewer_user_id=user.id)
    except DeleteMovieCardNotFoundError:
        raise HTTPException(status_code=404, detail='movie card not found') from None
    except DeleteMovieCardForbiddenError:
        raise HTTPException(status_code=403, detail='forbidden') from None
    return Response(status_code=204)


@router.post(
    '/{card_id}/share',
    response_model=ShareCardResponse,
    summary='Отправить карточку подписчикам в Telegram',
)
async def share_movie_card(
    card_id: int,
    body: ShareCardRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> ShareCardResponse:
    try:
        outcome = await ShareMovieCardService(db).execute(
            actor_user_id=user.id,
            card_id=card_id,
            recipient_user_ids=list(body.recipient_user_ids),
        )
    except MovieCardNotFoundForShareError:
        raise HTTPException(status_code=404, detail='movie card not found') from None
    except ShareMovieCardForbiddenError:
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

    for rid in outcome.recipient_ids:
        celery_application.tasks['tasks.telegram_engagement.deliver_shared_movie_card'].delay(
            actor_user_id=str(user.id),
            card_id=card_id,
            recipient_user_id=str(rid),
        )

    return ShareCardResponse(queued=len(outcome.recipient_ids))


@router.get(
    '/{card_id}/comments',
    response_model=MovieCardCommentListResponse,
    summary='Получить комментарии карточки',
)
async def list_card_comments(
    card_id: int,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: int | None = Query(default=None, ge=1),
    limit: int = Query(default=20, ge=1),
) -> MovieCardCommentListResponse:
    try:
        page = await ListMovieCardCommentsService(db).execute(
            viewer.id,
            card_id=card_id,
            parent_comment_id=None,
            cursor=cursor,
            limit=min(limit, 50),
            flat=True,
        )
    except ListCommentsMovieCardNotFoundError:
        raise HTTPException(status_code=404, detail='movie card not found') from None
    return MovieCardCommentListResponse(
        items=[_comment_item_to_response(item) for item in page.items],
        next_cursor=page.next_cursor,
    )


@router.get(
    '/{card_id}/comments/{comment_id}/replies',
    response_model=MovieCardCommentListResponse,
    summary='Получить ответы на комментарий',
)
async def list_card_comment_replies(
    card_id: int,
    comment_id: int,
    viewer: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
    cursor: int | None = Query(default=None, ge=1),
    limit: int = Query(default=20, ge=1),
) -> MovieCardCommentListResponse:
    try:
        page = await ListMovieCardCommentsService(db).execute(
            viewer.id,
            card_id=card_id,
            parent_comment_id=comment_id,
            cursor=cursor,
            limit=min(limit, 50),
        )
    except ListCommentsMovieCardNotFoundError:
        raise HTTPException(status_code=404, detail='movie card not found') from None
    except CommentNotFoundError:
        raise HTTPException(status_code=404, detail='comment not found') from None
    return MovieCardCommentListResponse(
        items=[_comment_item_to_response(item) for item in page.items],
        next_cursor=page.next_cursor,
    )


@router.post(
    '/{card_id}/comments',
    response_model=MovieCardCommentResponse,
    summary='Создать комментарий карточки',
)
async def create_card_comment(
    card_id: int,
    body: MovieCardCommentCreateRequest,
    user: CurrentUser,
    db: Annotated[AsyncSession, Depends(get_db)],
) -> MovieCardCommentResponse:
    try:
        created = await CreateMovieCardCommentService(db).execute(
            card_id,
            user.id,
            CreateMovieCardCommentInput(
                text=body.text,
                parent_comment_id=body.parent_comment_id,
            ),
        )
    except CommentMovieCardNotFoundError:
        raise HTTPException(status_code=404, detail='movie card not found') from None
    except ParentCommentNotFoundError:
        raise HTTPException(status_code=404, detail='parent comment not found') from None
    except ParentCommentMismatchError:
        raise HTTPException(
            status_code=422, detail='parent comment belongs to another card'
        ) from None
    except MovieCardCommentValidationError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

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

    return await _load_comment_response(db, created.id, user.id)
