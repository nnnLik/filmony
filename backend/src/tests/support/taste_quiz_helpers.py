from __future__ import annotations

from uuid import UUID

from core.database import get_session_factory
from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from models.user import User
from models.user_card import UserCard
from models.user_subscription import UserSubscription
from tests.support.user_card_category import ensure_default_category


async def seed_rated_cards_for_owner(
    *,
    owner_user_id: UUID,
    count: int,
    kinopoisk_id_base: int = 880_000,
    rating: float = 8.0,
) -> list[int]:
    """Seed ``count`` meaningful rated cards (not planned, rating >= 1)."""
    session_factory = get_session_factory()
    card_ids: list[int] = []
    async with session_factory() as session:
        category_id = await ensure_default_category(session, owner_user_id)
        for index in range(count):
            kinopoisk_id = kinopoisk_id_base + index
            film = Film(
                kinopoisk_id=kinopoisk_id,
                title=f'Taste Quiz Film {index}',
                year=2020 + (index % 5),
                poster_url=f'https://example.com/tq-{index}.jpg',
                genres=[],
            )
            session.add(film)
            await session.flush()
            session.add(
                CatalogItem(
                    provider=CatalogProvider.kinopoisk,
                    external_id=str(kinopoisk_id),
                    film_id=film.id,
                )
            )
            card = UserCard(
                user_id=owner_user_id,
                film_id=film.id,
                category_id=category_id,
                provider=CatalogProvider.kinopoisk,
                external_id=str(kinopoisk_id),
                rating=rating,
                company='alone',
                mood_before='relax',
                mood_after='enjoyed',
                is_planned=False,
            )
            session.add(card)
            await session.flush()
            card_ids.append(card.id)
        await session.commit()
    return card_ids


async def add_follow(*, follower_user_id: UUID, following_user_id: UUID) -> None:
    session_factory = get_session_factory()
    async with session_factory() as session:
        session.add(
            UserSubscription(
                follower_user_id=follower_user_id,
                following_user_id=following_user_id,
            )
        )
        await session.commit()


async def create_user(*, telegram_user_id: int, slug: str) -> User:
    session_factory = get_session_factory()
    async with session_factory() as session:
        user = User(
            telegram_user_id=telegram_user_id,
            profile_slug=slug,
            username=None,
            first_name=None,
            last_name=None,
            photo_url=None,
            display_name=None,
            bio=None,
            language_code=None,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user
