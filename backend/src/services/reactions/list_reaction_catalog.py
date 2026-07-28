from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from conf.settings import settings
from const.reaction_packs import REACTION_TAB_ORDER
from models.reaction_type import ReactionType
from utils.reaction_urls import resolve_reaction_media_url


@dataclass(frozen=True, slots=True)
class ReactionCatalogItem:
    id: int
    image_url: str
    category_slug: str
    asset_key: str


@dataclass(frozen=True, slots=True)
class ReactionCatalogTab:
    category_slug: str
    label: str
    items: tuple[ReactionCatalogItem, ...]


@dataclass(frozen=True, slots=True)
class ReactionCatalogGrouped:
    tabs: tuple[ReactionCatalogTab, ...]


def _row(rt: ReactionType) -> ReactionCatalogItem:
    base = settings.reaction_media.public_base_url
    return ReactionCatalogItem(
        id=int(rt.id),
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

    async def execute(self) -> ReactionCatalogGrouped:
        all_rows = (
            (await self._session.execute(select(ReactionType).order_by(ReactionType.id.asc())))
            .scalars()
            .all()
        )
        known_slugs = {tab.slug for tab in REACTION_TAB_ORDER}
        by_cat: dict[str, list[ReactionType]] = {}
        misc_bucket: list[ReactionType] = []
        for rt in all_rows:
            slug = rt.category_slug.strip()
            if slug in known_slugs:
                by_cat.setdefault(slug, []).append(rt)
            else:
                misc_bucket.append(rt)

        tabs: list[ReactionCatalogTab] = []
        for tab in REACTION_TAB_ORDER:
            bucket = by_cat.get(tab.slug, [])
            buckets_sorted = sorted(bucket, key=lambda r: (r.asset_key, r.id))
            items = tuple(_row(r) for r in buckets_sorted)
            tabs.append(
                ReactionCatalogTab(
                    category_slug=tab.slug,
                    label=tab.label_ru,
                    items=items,
                )
            )
        if misc_bucket:
            misc_sorted = sorted(misc_bucket, key=lambda r: (r.asset_key, r.id))
            tabs.append(
                ReactionCatalogTab(
                    category_slug='misc',
                    label='Без группы',
                    items=tuple(_row(r) for r in misc_sorted),
                )
            )

        return ReactionCatalogGrouped(tabs=tuple(tabs))


# Deprecated: prefer `ListReactionCatalogGroupedService` in new code.
ListReactionCatalogService = ListReactionCatalogGroupedService
