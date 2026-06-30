from __future__ import annotations

import asyncio
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from models.card_tag import CardTag
from models.catalog_item import CatalogItem, CatalogProvider
from models.film import Film
from models.game import Game
from models.user import User
from models.user_card import UserCard
from models.user_card_category import DEFAULT_USER_CARD_CATEGORY_NAME, UserCardCategory
from models.watchlist_entry import WatchlistEntry
from services.cards.card_catalog_release_fields import universal_release_year_date
from services.cards.list_user_card_comments import UserCardCommentAuthor
from services.reactions import GetReactionSummariesForTargetsService
from services.reactions.types import ReactionTargetSummary
from services.watchlist.watchlist_card_id import watchlist_card_id_from_user_card


@dataclass(frozen=True, slots=True)
class PlannedWatchPartner(UserCardCommentAuthor):
    has_rated: bool
    rating: float | None
    rated_user_card_id: int | None
    planned_user_card_id: int | None


@dataclass(frozen=True, slots=True)
class UserCardDetails:
    id: int
    user_id: UUID
    card_author: UserCardCommentAuthor
    provider: CatalogProvider
    external_id: str | None
    film_id: int | None
    film_kinopoisk_id: int | None
    film_genres: list[str]
    film_title: str
    film_year: int | None
    film_poster_url: str | None
    film_short_description: str | None
    film_description: str | None
    catalog_item_id: int | None
    display_title: str
    display_cover_url: str | None
    display_summary: str | None
    release_year: int | None
    release_date: str | None
    rating: float
    company: str
    mood_before: str
    mood_after: str
    watch_note: str
    custom_tags: list[str]
    category_id: int
    category_name: str
    reactions: ReactionTargetSummary
    is_favorite: bool
    is_planned: bool
    audio_url: str | None
    planned_watch_partners: list[PlannedWatchPartner]
    watchlist_entry_id: int | None


class UserCardNotFoundError(Exception):
    pass


class GetUserCardDetailsService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, card_id: int, viewer_user_id: UUID) -> UserCardDetails:
        film_pk = func.coalesce(UserCard.film_id, CatalogItem.film_id)
        row = (
            await self._session.execute(
                select(UserCard, User, Film, Game)
                .join(User, User.id == UserCard.user_id)
                .outerjoin(CatalogItem, CatalogItem.id == UserCard.catalog_item_id)
                .outerjoin(Film, Film.id == film_pk)
                .outerjoin(Game, Game.id == CatalogItem.game_id)
                .where(UserCard.id == card_id)
            )
        ).one_or_none()
        if row is None:
            raise UserCardNotFoundError()
        card, author, film, game = row

        display_title = (card.display_title or '').strip()
        if not display_title and film is not None:
            display_title = (film.title or '').strip()
        if not display_title:
            display_title = 'Untitled'

        film_title_deprecated = film.title if film is not None else display_title

        tags_result, cat_row_result, summaries_bundle = await asyncio.gather(
            self._session.execute(
                select(CardTag.tag).where(CardTag.card_id == card.id).order_by(CardTag.tag),
            ),
            self._session.execute(
                select(UserCardCategory).where(UserCardCategory.id == card.category_id),
            ),
            GetReactionSummariesForTargetsService(self._session).execute(
                viewer_user_id=viewer_user_id,
                user_card_ids=[card.id],
                comment_ids=[],
                feed_post_comment_ids=[],
                feed_post_ids=[],
            ),
        )
        tags = tags_result.scalars().all()
        cat_row = cat_row_result.scalar_one_or_none()
        category_name = cat_row.name if cat_row is not None else DEFAULT_USER_CARD_CATEGORY_NAME
        summaries, _, _, _ = summaries_bundle
        film_year_val = film.year if film is not None else None
        release_year, release_date = universal_release_year_date(
            film_year=film_year_val,
            game_released=game.released if game is not None else None,
        )
        planned_watch_partners, watchlist_entry_id = await self._load_planned_watchlist_context(
            card,
            viewer_user_id,
        )
        return UserCardDetails(
            id=card.id,
            user_id=card.user_id,
            card_author=UserCardCommentAuthor(
                id=author.id,
                profile_slug=author.profile_slug,
                username=author.username,
                first_name=author.first_name,
                last_name=author.last_name,
                photo_url=author.photo_url,
                display_name=author.display_name,
            ),
            provider=card.provider,
            external_id=card.external_id,
            film_id=film.id if film is not None else None,
            film_kinopoisk_id=film.kinopoisk_id if film is not None else None,
            film_genres=list(film.genres or []) if film is not None else [],
            film_title=film_title_deprecated,
            film_year=film_year_val,
            film_poster_url=film.poster_url if film is not None else None,
            film_short_description=film.short_description if film is not None else None,
            film_description=film.description if film is not None else None,
            catalog_item_id=card.catalog_item_id,
            display_title=display_title,
            display_cover_url=card.display_cover_url,
            display_summary=card.display_summary,
            release_year=release_year,
            release_date=release_date,
            rating=float(card.rating),
            company=card.company,
            mood_before=card.mood_before,
            mood_after=card.mood_after,
            watch_note=card.watch_note or '',
            custom_tags=list(tags),
            category_id=int(card.category_id),
            category_name=category_name,
            reactions=summaries[card.id],
            is_favorite=bool(card.is_favorite),
            is_planned=bool(card.is_planned),
            audio_url=card.audio_url,
            planned_watch_partners=planned_watch_partners,
            watchlist_entry_id=watchlist_entry_id,
        )

    @staticmethod
    def _is_rated_user_card(card: UserCard) -> bool:
        return not card.is_planned and float(card.rating) >= 1.0

    @staticmethod
    def _is_planned_user_card(card: UserCard) -> bool:
        return bool(card.is_planned)

    def _partner_title_match(self, card: UserCard):
        if card.film_id is not None:
            return UserCard.film_id == card.film_id
        if card.catalog_item_id is not None:
            return UserCard.catalog_item_id == card.catalog_item_id
        display_title = (card.display_title or '').strip()
        if display_title:
            return (
                UserCard.provider == card.provider,
                UserCard.display_title == display_title,
            )
        return None

    async def _load_planned_watchlist_context(
        self,
        card: UserCard,
        viewer_user_id: UUID,
    ) -> tuple[list[PlannedWatchPartner], int | None]:
        if not card.is_planned:
            return [], None
        watchlist_card_id = watchlist_card_id_from_user_card(card)
        if watchlist_card_id is None:
            return [], None
        entry = (
            await self._session.execute(
                select(WatchlistEntry).where(
                    WatchlistEntry.user_id == card.user_id,
                    WatchlistEntry.card_id == watchlist_card_id,
                )
            )
        ).scalar_one_or_none()
        if entry is None:
            return [], None

        watchlist_entry_id: int | None = None
        if card.user_id == viewer_user_id:
            watchlist_entry_id = int(entry.id)

        partner_ids: list[UUID] = []
        seen: set[UUID] = {card.user_id}
        for raw in entry.watch_with_user_ids or []:
            try:
                partner_id = UUID(str(raw))
            except (TypeError, ValueError):
                continue
            if partner_id in seen:
                continue
            seen.add(partner_id)
            partner_ids.append(partner_id)
        if entry.watch_with_user_id is not None and entry.watch_with_user_id not in seen:
            partner_ids.append(entry.watch_with_user_id)

        if not partner_ids:
            return [], watchlist_entry_id

        users = (
            (
                await self._session.execute(
                    select(User).where(User.id.in_(partner_ids)),
                )
            )
            .scalars()
            .all()
        )
        users_by_id = {user.id: user for user in users}

        title_match = self._partner_title_match(card)
        rated_by_user: dict[UUID, UserCard] = {}
        planned_by_user: dict[UUID, UserCard] = {}
        if title_match is not None:
            match_cond = title_match if not isinstance(title_match, tuple) else and_(*title_match)
            partner_cards = (
                (
                    await self._session.execute(
                        select(UserCard)
                        .where(UserCard.user_id.in_(partner_ids))
                        .where(match_cond)
                        .order_by(UserCard.id.desc()),
                    )
                )
                .scalars()
                .all()
            )
            for partner_card in partner_cards:
                if self._is_planned_user_card(partner_card) and partner_card.user_id not in planned_by_user:
                    planned_by_user[partner_card.user_id] = partner_card
                elif self._is_rated_user_card(partner_card) and partner_card.user_id not in rated_by_user:
                    rated_by_user[partner_card.user_id] = partner_card

        partners: list[PlannedWatchPartner] = []
        for partner_id in partner_ids:
            user = users_by_id.get(partner_id)
            if user is None:
                continue
            rated = rated_by_user.get(partner_id)
            planned = planned_by_user.get(partner_id)
            has_rated = rated is not None
            partners.append(
                PlannedWatchPartner(
                    id=user.id,
                    profile_slug=user.profile_slug,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    photo_url=user.photo_url,
                    display_name=user.display_name,
                    has_rated=has_rated,
                    rating=float(rated.rating) if rated is not None else None,
                    rated_user_card_id=int(rated.id) if rated is not None else None,
                    planned_user_card_id=(
                        int(planned.id) if planned is not None and not has_rated else None
                    ),
                )
            )
        return partners, watchlist_entry_id
