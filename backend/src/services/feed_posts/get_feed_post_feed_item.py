from __future__ import annotations

from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.feed_post import FeedPost
from models.film import Film
from models.user import User
from models.user_card import UserCard
from services.cards.list_movie_card_comments import MovieCardCommentAuthor
from services.cards.list_movie_card_feed import (
    FeedPostFeedItem,
    FeedPostReferencedCardSnippet,
    attach_feed_post_list_engagement,
)
from services.feed_posts.get_feed_post_by_id import FeedPostNotFoundError


class GetFeedPostFeedItemService:
    """Загружает пост ленты с автором и сниппетом связанной карточки — как элемент ленты."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(session=session)

    async def execute(self, post_id: int, viewer_user_id: UUID) -> FeedPostFeedItem:
        row = (
            await self._session.execute(
                select(FeedPost, User)
                .join(User, User.id == FeedPost.user_id)
                .where(FeedPost.id == post_id)
            )
        ).one_or_none()
        if row is None:
            raise FeedPostNotFoundError()
        fp, author_user = row

        ref_snippet: FeedPostReferencedCardSnippet | None = None
        rid = fp.referenced_card_id
        if rid is not None:
            rq = (
                select(UserCard, Film)
                .join(Film, Film.id == UserCard.film_id)
                .where(UserCard.id == int(rid))
            )
            ref_row = (await self._session.execute(rq)).one_or_none()
            if ref_row is not None:
                mc, fl = ref_row
                ref_snippet = FeedPostReferencedCardSnippet(
                    movie_card_id=int(mc.id),
                    film_title=str(fl.title),
                    film_year=fl.year,
                    film_poster_url=fl.poster_url,
                    rating=float(mc.rating),
                )

        author = MovieCardCommentAuthor(
            id=author_user.id,
            profile_slug=author_user.profile_slug,
            username=author_user.username,
            first_name=author_user.first_name,
            last_name=author_user.last_name,
            photo_url=author_user.photo_url,
            display_name=author_user.display_name,
        )
        base = FeedPostFeedItem(
            id=int(fp.id),
            user_id=fp.user_id,
            author=author,
            body=fp.body or '',
            image_url=fp.image_url,
            referenced_movie_card_id=int(rid) if rid is not None else None,
            source_comment_id=int(fp.source_comment_id)
            if fp.source_comment_id is not None
            else None,
            created_at=fp.created_at,
            feed_source='feed_posts',
            referenced_card=ref_snippet,
        )
        enriched = await attach_feed_post_list_engagement(self._session, viewer_user_id, [base])
        return enriched[0]
