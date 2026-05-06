from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ReactionPackTab:
    slug: str
    label_ru: str
    directory: str


REACTION_TAB_ORDER: tuple[ReactionPackTab, ...] = (
    ReactionPackTab(
        slug='pepe',
        label_ru='Pepe',
        directory='25781-pepe-emojigg-pack',
    ),
    ReactionPackTab(
        slug='meme_pt1',
        label_ru='Мемы I',
        directory='57442-meme-pt1-emojigg-pack',
    ),
    ReactionPackTab(
        slug='cats',
        label_ru='Котики',
        directory='80599-cats-emojigg-pack',
    ),
    ReactionPackTab(
        slug='cat_memes',
        label_ru='Cat memes',
        directory='89312-cat-memes-essentials-emojigg-pack',
    ),
    ReactionPackTab(
        slug='frieren',
        label_ru='Фриерен',
        directory='643214-frieren-emojigg-pack',
    ),
)


def slug_by_emoji_directory(directory: str) -> str | None:
    for tab in REACTION_TAB_ORDER:
        if tab.directory == directory:
            return tab.slug
    return None


def reaction_tab_slug_order_index() -> dict[str, int]:
    return {tab.slug: i for i, tab in enumerate(REACTION_TAB_ORDER)}
