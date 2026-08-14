from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.film import Film
from models.user import User
from models.watch_party import WatchParty
from services.subscriptions.list_following_user_ids_for_follower_user import (
    ListFollowingUserIdsForFollowerUserService,
)
from services.watch_parties.batch_user_watching import BatchUserWatchingService


@dataclass(frozen=True, slots=True)
class FollowingWatchingNowItemDTO:
    user_id: UUID
    display_name: str
    photo_url: str | None
    slug: str
    film_id: int
    film_title: str
    film_poster_url: str | None
    invite_slug: str | None
    party_id: UUID | None


@dataclass
class ListFollowingWatchingNowService:
    """Lists followed users who are actively watching a film right now."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, actor_user_id: UUID) -> list[FollowingWatchingNowItemDTO]:
        following_ids = await ListFollowingUserIdsForFollowerUserService.build(
            self._session,
        ).execute(actor_user_id)
        following_ids = following_ids[:100]
        if not following_ids:
            return []

        watching = await BatchUserWatchingService.build().execute(list(following_ids))
        if not watching:
            return []

        ordered_user_ids = [user_id for user_id in following_ids if user_id in watching]

        users_result = await self._session.execute(
            select(User).where(User.id.in_(ordered_user_ids)),
        )
        users_by_id = {user.id: user for user in users_result.scalars().all()}

        party_ids = [item.party_id for item in watching.values() if item.party_id is not None]
        parties_by_id: dict[UUID, WatchParty] = {}
        film_posters_by_party_id: dict[UUID, str | None] = {}
        if party_ids:
            parties_result = await self._session.execute(
                select(WatchParty, Film.poster_url)
                .join(Film, Film.id == WatchParty.film_id)
                .where(WatchParty.id.in_(party_ids)),
            )
            for party, poster_url in parties_result.all():
                parties_by_id[party.id] = party
                film_posters_by_party_id[party.id] = poster_url

        film_ids_without_party = {
            item.film_id
            for user_id, item in watching.items()
            if item.party_id is None and user_id in ordered_user_ids
        }
        posters_by_film_id: dict[int, str | None] = {}
        if film_ids_without_party:
            films_result = await self._session.execute(
                select(Film.id, Film.poster_url).where(Film.id.in_(film_ids_without_party)),
            )
            posters_by_film_id = dict(films_result.all())

        out: list[FollowingWatchingNowItemDTO] = []
        for user_id in ordered_user_ids:
            user = users_by_id.get(user_id)
            watch_item = watching.get(user_id)
            if user is None or watch_item is None:
                continue

            party_id = watch_item.party_id
            invite_slug: str | None = None
            film_poster_url: str | None = None
            if party_id is not None:
                party = parties_by_id.get(party_id)
                invite_slug = party.invite_slug if party is not None else None
                film_poster_url = film_posters_by_party_id.get(party_id)
            else:
                film_poster_url = posters_by_film_id.get(watch_item.film_id)

            display_name = (user.display_name or user.profile_slug or 'Пользователь').strip()

            out.append(
                FollowingWatchingNowItemDTO(
                    user_id=user_id,
                    display_name=display_name,
                    photo_url=user.photo_url,
                    slug=user.profile_slug,
                    film_id=watch_item.film_id,
                    film_title=watch_item.film_title,
                    film_poster_url=film_poster_url,
                    invite_slug=invite_slug,
                    party_id=party_id,
                ),
            )
        return out
