"""Service coverage for user card comment update and delete."""

from __future__ import annotations

from uuid import UUID

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from core.database import get_session_factory
from models.card_comment import CardComment
from models.card_enums import CardCompany, CardMoodAfter, CardMoodBefore
from models.film import Film
from models.user import User
from models.user_card import UserCard
from services.cards.create_user_card import CreateUserCardInput, CreateUserCardService
from services.cards.delete_user_card_comment import (
    DeleteUserCardCommentService,
)
from services.cards.delete_user_card_comment import (
    UserCardCommentForbiddenError as DeleteUserCardCommentForbiddenError,
)
from services.cards.delete_user_card_comment import (
    UserCardCommentMismatchError as DeleteUserCardCommentMismatchError,
)
from services.cards.delete_user_card_comment import (
    UserCardCommentNotFoundError as DeleteUserCardCommentNotFoundError,
)
from services.cards.update_user_card_comment import (
    UpdateUserCardCommentService,
    UserCardCommentForbiddenError,
    UserCardCommentMismatchError,
    UserCardCommentNotFoundError,
    UserCardCommentValidationError,
)
from tests.support.user_card_category import ensure_default_category


async def _create_user(*, telegram_user_id: int) -> User:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            telegram_user_id=telegram_user_id,
            profile_slug=f'ucc-{telegram_user_id}',
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user


async def _create_film(*, kinopoisk_id: int) -> Film:
    session_factory = get_session_factory()
    async with session_factory() as session:
        film = Film(
            kinopoisk_id=kinopoisk_id,
            title='Comment Service Film',
            year=2024,
            poster_url='https://example.com/p.jpg',
            genres=['драма'],
        )
        session.add(film)
        await session.commit()
        await session.refresh(film)
        return film


async def _create_card(user_id: UUID, film: Film) -> UserCard:
    session_factory = get_session_factory()
    async with session_factory() as session:
        await ensure_default_category(session, user_id)
        card = await CreateUserCardService(session).execute(
            user_id,
            CreateUserCardInput(
                film_id=film.id,
                kinopoisk_id=film.kinopoisk_id,
                rating=8.0,
                company=CardCompany.alone,
                mood_before=CardMoodBefore.relax,
                mood_after=CardMoodAfter.enjoyed,
                custom_tags=[],
                watch_note='',
                genres=film.genres or [],
            ),
        )
        await session.commit()
        return card


async def _create_comment(
    *,
    card_id: int,
    user_id: UUID,
    text: str = 'hello',
    image_url: str | None = None,
) -> CardComment:
    session_factory = get_session_factory()
    async with session_factory() as session:
        comment = CardComment(
            card_id=card_id,
            user_id=user_id,
            text=text,
            image_url=image_url,
        )
        session.add(comment)
        await session.commit()
        await session.refresh(comment)
        return comment


@pytest.mark.asyncio
async def test_update_comment_not_found(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=890001)
    film = await _create_film(kinopoisk_id=890001)
    card = await _create_card(user.id, film)
    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = UpdateUserCardCommentService.build(session)
        with pytest.raises(UserCardCommentNotFoundError):
            await svc.execute(
                card_id=card.id,
                comment_id=999999,
                actor_user_id=user.id,
                text='nope',
            )


@pytest.mark.asyncio
async def test_update_comment_card_mismatch(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=890002)
    film = await _create_film(kinopoisk_id=890002)
    card = await _create_card(user.id, film)
    comment = await _create_comment(card_id=card.id, user_id=user.id)
    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = UpdateUserCardCommentService.build(session)
        with pytest.raises(UserCardCommentMismatchError):
            await svc.execute(
                card_id=card.id + 999,
                comment_id=comment.id,
                actor_user_id=user.id,
                text='wrong card',
            )


@pytest.mark.asyncio
async def test_update_comment_forbidden(async_client: AsyncClient) -> None:
    owner = await _create_user(telegram_user_id=890003)
    other = await _create_user(telegram_user_id=890004)
    film = await _create_film(kinopoisk_id=890003)
    card = await _create_card(owner.id, film)
    comment = await _create_comment(card_id=card.id, user_id=owner.id)
    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = UpdateUserCardCommentService.build(session)
        with pytest.raises(UserCardCommentForbiddenError):
            await svc.execute(
                card_id=card.id,
                comment_id=comment.id,
                actor_user_id=other.id,
                text='hack',
            )


@pytest.mark.asyncio
async def test_update_comment_invalid_image_url(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=890005)
    film = await _create_film(kinopoisk_id=890005)
    card = await _create_card(user.id, film)
    comment = await _create_comment(card_id=card.id, user_id=user.id)
    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = UpdateUserCardCommentService.build(session)
        with pytest.raises(UserCardCommentValidationError, match='invalid image_url'):
            await svc.execute(
                card_id=card.id,
                comment_id=comment.id,
                actor_user_id=user.id,
                text='pic',
                image_url='https://example.com/x.jpg',
            )


@pytest.mark.asyncio
async def test_update_comment_clear_image_and_text_only(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=890006)
    film = await _create_film(kinopoisk_id=890006)
    card = await _create_card(user.id, film)
    media_url = '/api/feed-posts/media/user_media/movie_card_comments/x/y.webp'
    comment = await _create_comment(
        card_id=card.id,
        user_id=user.id,
        text='old',
        image_url=media_url,
    )
    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = UpdateUserCardCommentService.build(session)
        updated = await svc.execute(
            card_id=card.id,
            comment_id=comment.id,
            actor_user_id=user.id,
            text='  refreshed  ',
            clear_image=True,
        )
        assert updated.text == 'refreshed'
        assert updated.image_url is None


@pytest.mark.asyncio
async def test_update_comment_keeps_image_when_not_provided(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=890007)
    film = await _create_film(kinopoisk_id=890007)
    card = await _create_card(user.id, film)
    media_url = '/api/feed-posts/media/user_media/movie_card_comments/x/y.webp'
    comment = await _create_comment(
        card_id=card.id,
        user_id=user.id,
        text='with image',
        image_url=media_url,
    )
    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = UpdateUserCardCommentService.build(session)
        updated = await svc.execute(
            card_id=card.id,
            comment_id=comment.id,
            actor_user_id=user.id,
            text='still has image',
        )
        assert updated.image_url == media_url


@pytest.mark.asyncio
async def test_update_comment_empty_text_without_image_rejected(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=890008)
    film = await _create_film(kinopoisk_id=890008)
    card = await _create_card(user.id, film)
    comment = await _create_comment(card_id=card.id, user_id=user.id, text='text only')
    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = UpdateUserCardCommentService.build(session)
        with pytest.raises(UserCardCommentValidationError, match='text or image_url is required'):
            await svc.execute(
                card_id=card.id,
                comment_id=comment.id,
                actor_user_id=user.id,
                text='   ',
                clear_image=True,
            )


@pytest.mark.asyncio
async def test_update_comment_empty_text_preserves_image(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=890013)
    film = await _create_film(kinopoisk_id=890013)
    card = await _create_card(user.id, film)
    media_url = '/api/feed-posts/media/user_media/movie_card_comments/x/y.webp'
    comment = await _create_comment(
        card_id=card.id,
        user_id=user.id,
        text='caption',
        image_url=media_url,
    )
    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = UpdateUserCardCommentService.build(session)
        updated = await svc.execute(
            card_id=card.id,
            comment_id=comment.id,
            actor_user_id=user.id,
            text='   ',
        )
        assert updated.text == ''
        assert updated.image_url == media_url


@pytest.mark.asyncio
async def test_update_comment_invalid_reaction_token(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=890014)
    film = await _create_film(kinopoisk_id=890014)
    card = await _create_card(user.id, film)
    comment = await _create_comment(card_id=card.id, user_id=user.id)
    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = UpdateUserCardCommentService.build(session)
        with pytest.raises(UserCardCommentValidationError):
            await svc.execute(
                card_id=card.id,
                comment_id=comment.id,
                actor_user_id=user.id,
                text='⟦@missing_slug⟧',
            )

    user = await _create_user(telegram_user_id=890009)
    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = DeleteUserCardCommentService.build(session)
        with pytest.raises(DeleteUserCardCommentNotFoundError):
            await svc.execute(
                card_id=1,
                comment_id=999999,
                actor_user_id=user.id,
            )


@pytest.mark.asyncio
async def test_delete_comment_mismatch_and_forbidden(async_client: AsyncClient) -> None:
    owner = await _create_user(telegram_user_id=890010)
    other = await _create_user(telegram_user_id=890011)
    film = await _create_film(kinopoisk_id=890010)
    card = await _create_card(owner.id, film)
    comment = await _create_comment(card_id=card.id, user_id=owner.id)
    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = DeleteUserCardCommentService.build(session)
        with pytest.raises(DeleteUserCardCommentMismatchError):
            await svc.execute(
                card_id=card.id + 1,
                comment_id=comment.id,
                actor_user_id=owner.id,
            )
        with pytest.raises(DeleteUserCardCommentForbiddenError):
            await svc.execute(
                card_id=card.id,
                comment_id=comment.id,
                actor_user_id=other.id,
            )


@pytest.mark.asyncio
async def test_delete_comment_success(async_client: AsyncClient) -> None:
    user = await _create_user(telegram_user_id=890012)
    film = await _create_film(kinopoisk_id=890012)
    card = await _create_card(user.id, film)
    comment = await _create_comment(card_id=card.id, user_id=user.id)
    session_factory = get_session_factory()
    async with session_factory() as session:
        svc = DeleteUserCardCommentService.build(session)
        await svc.execute(
            card_id=card.id,
            comment_id=comment.id,
            actor_user_id=user.id,
        )
        gone = (
            await session.execute(select(CardComment).where(CardComment.id == comment.id))
        ).scalar_one_or_none()
        assert gone is None
