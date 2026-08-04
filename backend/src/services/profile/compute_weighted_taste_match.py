from __future__ import annotations

from dataclasses import dataclass
from typing import Self
from uuid import UUID

from sqlalchemy import select, union
from sqlalchemy.ext.asyncio import AsyncSession

from models.card_tag import CardTag
from models.user import User
from models.user_card import UserCard
from models.user_subscription import UserSubscription

TASTE_PEERS_LIMIT = 5
MIN_PEER_RATED_CARDS = 3
MIN_SHARED_FOR_RATING_AGREEMENT = 3
RATING_SCALE_MAX_DELTA = 9.0

WEIGHT_JACCARD_TITLES = 0.35
WEIGHT_TAG_OVERLAP = 0.25
WEIGHT_RATING_AGREEMENT = 0.25
WEIGHT_FAVORITES_JACCARD = 0.15


@dataclass(frozen=True, slots=True)
class TasteMatchBreakdown:
    shared_titles: float
    tag_overlap: float
    rating_agreement: float
    shared_favorites: float


@dataclass(frozen=True, slots=True)
class WeightedTastePeerItem:
    id: UUID
    profile_slug: str
    display_name: str | None
    photo_url: str | None
    similarity_score: float
    score_v2: float
    breakdown: TasteMatchBreakdown
    shared_films_count: int


@dataclass(frozen=True, slots=True)
class _ProfileCardSnapshot:
    film_id: int | None
    catalog_item_id: int | None
    rating: float
    is_favorite: bool
    tags: frozenset[str]


def _title_identity(card: _ProfileCardSnapshot) -> str | None:
    if card.catalog_item_id is not None:
        return f'c:{card.catalog_item_id}'
    if card.film_id is not None:
        return f'f:{card.film_id}'
    return None


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 0.0
    union_size = len(a | b)
    if union_size == 0:
        return 0.0
    return len(a & b) / union_size


def _film_jaccard_v1(owner_films: set[int], peer_films: set[int]) -> tuple[float, int]:
    shared = len(owner_films & peer_films)
    union_size = len(owner_films | peer_films)
    if union_size == 0:
        return 0.0, shared
    return round(shared / union_size, 3), shared


def _rating_agreement(
    owner_by_title: dict[str, float],
    peer_by_title: dict[str, float],
    shared_titles: set[str],
) -> float:
    if len(shared_titles) < MIN_SHARED_FOR_RATING_AGREEMENT:
        return 0.0
    deltas = [abs(owner_by_title[key] - peer_by_title[key]) for key in shared_titles]
    avg_delta = sum(deltas) / len(deltas)
    return round(max(0.0, 1.0 - avg_delta / RATING_SCALE_MAX_DELTA), 3)


def _compute_score_v2(breakdown: TasteMatchBreakdown) -> float:
    score = (
        WEIGHT_JACCARD_TITLES * breakdown.shared_titles
        + WEIGHT_TAG_OVERLAP * breakdown.tag_overlap
        + WEIGHT_RATING_AGREEMENT * breakdown.rating_agreement
        + WEIGHT_FAVORITES_JACCARD * breakdown.shared_favorites
    )
    return round(score, 3)


@dataclass
class ComputeWeightedTasteMatchService:
    """Ranks taste peers in the owner's network using a weighted multi-signal score."""

    _session: AsyncSession

    @classmethod
    def build(cls, session: AsyncSession) -> Self:
        return cls(_session=session)

    async def execute(self, owner_id: UUID) -> list[WeightedTastePeerItem]:
        owner_cards = await self._load_profile_cards(owner_id)
        if not owner_cards:
            return []

        owner_titles = {_title_identity(c) for c in owner_cards}
        owner_titles.discard(None)
        if not owner_titles:
            return []

        owner_film_ids = {c.film_id for c in owner_cards if c.film_id is not None}
        owner_by_title = {
            key: c.rating for c in owner_cards if (key := _title_identity(c)) is not None
        }
        owner_tags: set[str] = set()
        for card in owner_cards:
            owner_tags.update(card.tags)
        owner_favorites = {
            key for c in owner_cards if c.is_favorite and (key := _title_identity(c)) is not None
        }

        peer_ids = await self._load_network_peer_ids(owner_id)
        if not peer_ids:
            return []

        peer_cards_by_user = await self._load_cards_by_users(peer_ids)
        users_by_id = await self._load_users(peer_ids)

        candidates: list[WeightedTastePeerItem] = []
        for peer_id in peer_ids:
            peer_cards = peer_cards_by_user.get(peer_id, [])
            if len(peer_cards) < MIN_PEER_RATED_CARDS:
                continue

            user = users_by_id.get(peer_id)
            if user is None:
                continue

            peer_titles = {_title_identity(c) for c in peer_cards}
            peer_titles.discard(None)
            shared_title_keys = owner_titles & peer_titles
            if not shared_title_keys:
                continue

            peer_film_ids = {c.film_id for c in peer_cards if c.film_id is not None}
            v1_score, _shared_film_count = _film_jaccard_v1(owner_film_ids, peer_film_ids)

            peer_by_title = {
                key: c.rating for c in peer_cards if (key := _title_identity(c)) is not None
            }
            peer_tags: set[str] = set()
            for card in peer_cards:
                peer_tags.update(card.tags)
            peer_favorites = {
                key for c in peer_cards if c.is_favorite and (key := _title_identity(c)) is not None
            }

            breakdown = TasteMatchBreakdown(
                shared_titles=round(_jaccard(owner_titles, peer_titles), 3),
                tag_overlap=round(_jaccard(owner_tags, peer_tags), 3),
                rating_agreement=_rating_agreement(
                    owner_by_title,
                    peer_by_title,
                    shared_title_keys,
                ),
                shared_favorites=round(_jaccard(owner_favorites, peer_favorites), 3),
            )
            candidates.append(
                WeightedTastePeerItem(
                    id=user.id,
                    profile_slug=user.profile_slug,
                    display_name=user.display_name,
                    photo_url=user.photo_url,
                    similarity_score=v1_score,
                    score_v2=_compute_score_v2(breakdown),
                    breakdown=breakdown,
                    shared_films_count=len(shared_title_keys),
                )
            )

        candidates.sort(
            key=lambda item: (-item.score_v2, -item.shared_films_count, str(item.id)),
        )
        return candidates[:TASTE_PEERS_LIMIT]

    async def _load_network_peer_ids(self, owner_id: UUID) -> list[UUID]:
        followers = select(UserSubscription.follower_user_id.label('peer_id')).where(
            UserSubscription.following_user_id == owner_id
        )
        following = select(UserSubscription.following_user_id.label('peer_id')).where(
            UserSubscription.follower_user_id == owner_id
        )
        network = union(followers, following).subquery()
        rows = (await self._session.execute(select(network.c.peer_id))).all()
        return [row[0] for row in rows]

    async def _load_users(self, user_ids: list[UUID]) -> dict[UUID, User]:
        if not user_ids:
            return {}
        rows = (
            (await self._session.execute(select(User).where(User.id.in_(user_ids)))).scalars().all()
        )
        return {user.id: user for user in rows}

    async def _load_profile_cards(self, user_id: UUID) -> list[_ProfileCardSnapshot]:
        return await self._load_cards_for_user(user_id)

    async def _load_cards_by_users(
        self,
        user_ids: list[UUID],
    ) -> dict[UUID, list[_ProfileCardSnapshot]]:
        if not user_ids:
            return {}

        card_rows = (
            await self._session.execute(
                select(
                    UserCard.user_id,
                    UserCard.id,
                    UserCard.film_id,
                    UserCard.catalog_item_id,
                    UserCard.rating,
                    UserCard.is_favorite,
                ).where(
                    UserCard.user_id.in_(user_ids),
                    UserCard.is_planned.is_(False),
                )
            )
        ).all()
        if not card_rows:
            return {}

        card_ids = [int(row.id) for row in card_rows]
        tag_rows = (
            await self._session.execute(
                select(CardTag.card_id, CardTag.tag).where(CardTag.card_id.in_(card_ids))
            )
        ).all()
        tags_by_card: dict[int, set[str]] = {}
        for card_id, tag in tag_rows:
            tags_by_card.setdefault(int(card_id), set()).add(tag.strip().lower())

        by_user: dict[UUID, list[_ProfileCardSnapshot]] = {uid: [] for uid in user_ids}
        for row in card_rows:
            snapshot = _ProfileCardSnapshot(
                film_id=int(row.film_id) if row.film_id is not None else None,
                catalog_item_id=int(row.catalog_item_id)
                if row.catalog_item_id is not None
                else None,
                rating=float(row.rating),
                is_favorite=bool(row.is_favorite),
                tags=frozenset(tags_by_card.get(int(row.id), set())),
            )
            if _title_identity(snapshot) is None:
                continue
            by_user[row.user_id].append(snapshot)
        return by_user

    async def _load_cards_for_user(self, user_id: UUID) -> list[_ProfileCardSnapshot]:
        by_user = await self._load_cards_by_users([user_id])
        return by_user.get(user_id, [])
