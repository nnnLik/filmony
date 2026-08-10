from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from services.watch_parties.watch_party_redis import batch_user_watching


@dataclass(frozen=True, slots=True)
class UserWatchingDTO:
    film_id: int
    film_title: str
    party_id: UUID | None


@dataclass
class BatchUserWatchingService:
    """Returns active watch-party presence for requested users from Redis."""

    @classmethod
    def build(cls) -> Self:
        return cls()

    async def execute(self, user_ids: list[UUID]) -> dict[UUID, UserWatchingDTO]:
        unique = list(dict.fromkeys(user_ids))[:100]
        raw = await batch_user_watching(unique)
        out: dict[UUID, UserWatchingDTO] = {}
        for user_id, payload in raw.items():
            film_id = payload.get('film_id')
            film_title = payload.get('film_title')
            if film_id is None or film_title is None:
                continue
            party_raw = payload.get('party_id')
            party_id = UUID(str(party_raw)) if party_raw else None
            out[user_id] = UserWatchingDTO(
                film_id=int(film_id),
                film_title=str(film_title),
                party_id=party_id,
            )
        return out
