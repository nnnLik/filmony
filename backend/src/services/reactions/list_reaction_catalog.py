from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from conf.settings import settings
from const.reaction_packs import REACTION_TAB_ORDER
from models.reaction_type import ReactionType
from models.user_recent_reaction import UserRecentReaction
from utils.reaction_urls import resolve_reaction_media_url


@dataclass(frozen=True, slots=True)
class ReactionCatalogItem:
    id: int
    label: str | None
    image_url: str
    category_slug: str | None
    asset_key: str | None


@dataclass(frozen=True, slots=True)
class ReactionCatalogTab:
    category_slug: str
    label: str
    items: tuple[ReactionCatalogItem, ...]


@dataclass(frozen=True, slots=True)
class ReactionCatalogGrouped:
    recent: tuple[ReactionCatalogItem, ...]
    tabs: tuple[ReactionCatalogTab, ...]


def _row(rt: ReactionType) -> ReactionCatalogItem:
    base = settings.reaction_media.public_base_url
    return ReactionCatalogItem(
        id=int(rt.id),
        label=rt.label,
        image_url=resolve_reaction_media_url(
            asset_key=rt.asset_key,
            image_url_fallback=rt.image_url,
            public_base=base,
        ),
        category_slug=rt.category_slug,
        asset_key=rt.asset_key,
    )


class ListReactionCatalogGroupedService:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def execute(self, *, viewer_user_id: UUID | None) -> ReactionCatalogGrouped:
        all_active = (
            (
                await self._session.execute(
                    select(ReactionType)
                    .where(ReactionType.is_active.is_(True))
                    .order_by(ReactionType.sort_order.asc(), ReactionType.id.asc())
                )
            )
            .scalars()
            .all()
        )
        by_cat: dict[str, list[ReactionType]] = {}
        orphans: list[ReactionType] = []
        for rt in all_active:
            slug = (rt.category_slug or '').strip()
            if not slug:
                orphans.append(rt)
                continue
            by_cat.setdefault(slug, []).append(rt)

        tabs: list[ReactionCatalogTab] = []
        for tab in REACTION_TAB_ORDER:
            bucket = by_cat.get(tab.slug, [])
            buckets_sorted = sorted(bucket, key=lambda r: (r.sort_order, r.id))
            items = tuple(_row(r) for r in buckets_sorted)
            tabs.append(
                ReactionCatalogTab(
                    category_slug=tab.slug,
                    label=tab.label_ru,
                    items=items,
                )
            )
        if orphans:
            orphans_sorted = sorted(orphans, key=lambda r: (r.sort_order, r.id))
            tabs.append(
                ReactionCatalogTab(
                    category_slug='misc',
                    label='Без группы',
                    items=tuple(_row(r) for r in orphans_sorted),
                )
            )

        recent: tuple[ReactionCatalogItem, ...] = ()
        if viewer_user_id is not None:
            rrows = (
                (
                    await self._session.execute(
                        select(ReactionType)
                        .join(
                            UserRecentReaction,
                            UserRecentReaction.reaction_type_id == ReactionType.id,
                        )
                        .where(
                            UserRecentReaction.user_id == viewer_user_id,
                            ReactionType.is_active.is_(True),
                        )
                        .order_by(UserRecentReaction.last_used_at.desc())
                        .limit(48)
                    )
                )
                .scalars()
                .all()
            )
            recent = tuple(_row(r) for r in rrows)

        return ReactionCatalogGrouped(recent=recent, tabs=tuple(tabs))


# Back-compat alias для импортов вне API.
ListReactionCatalogService = ListReactionCatalogGroupedService
