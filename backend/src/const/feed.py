from __future__ import annotations

from typing import Final, Literal

FeedMode = Literal['default', 'subscriptions_only', 'subscribers_only']

StreamName = Literal[
    'subscriptions',
    'subscribers',
    'personal_affinity',
    'discovery',
    'feed_posts',
    'global',
]

# Сколько id максимум держим в каждом внутреннем потоке за один запрос (глубокая пагинация
# может исчерпать пул — см. docs/features/feed-recommendation-engine.md).
STREAM_POOL_LIMIT: Final[int] = 400

# Максимум card id в поле seen курсора ленты (хвост), чтобы payload не раздувался безлимитно.
FEED_CURSOR_SEEN_MAX: Final[int] = 2048

# Сколько свежих карточек сканировать под скоринг affinity до финальной сортировки.
AFFINITY_CANDIDATE_SCAN: Final[int] = 500

# Один слот из каждых N отдаётся каналу discovery (диапазон продукта 5–10).
DISCOVERY_EVERY_N_SLOTS: Final[int] = 8

# Не чаще чем раз в N слотов брать карточку с тем же автором или тем же фильмом, что уже
# в хвосте последних выдач (окно = K последних позиций). Свои карточки зрителя не режутся.
ANTI_SPAM_WINDOW: Final[int] = 2

GENRE_OVERLAP_WEIGHT: Final[int] = 2
TAG_OVERLAP_WEIGHT: Final[int] = 3

# Цикл слотов: соцграф + affinity + текстовые посты + discovery (детерминированное чередование).
SLOT_PATTERN: Final[tuple[StreamName, ...]] = (
    'subscriptions',
    'subscriptions',
    'subscribers',
    'subscriptions',
    'personal_affinity',
    'subscribers',
    'feed_posts',
    'discovery',
)

# Если у слота нет кандидата — пробуем источники в этом порядке.
FALLBACK_ORDER: Final[tuple[StreamName, ...]] = (
    'subscriptions',
    'subscribers',
    'personal_affinity',
    'feed_posts',
    'discovery',
)

STREAM_KEYS: Final[tuple[StreamName, ...]] = (
    'subscriptions',
    'subscribers',
    'personal_affinity',
    'discovery',
    'feed_posts',
)

VALID_FEED_MODES: Final[frozenset[str]] = frozenset(
    {'default', 'subscriptions_only', 'subscribers_only'}
)

ALLOWED_STREAMS_BY_MODE: Final[dict[FeedMode, frozenset[StreamName]]] = {
    'default': frozenset(STREAM_KEYS),
    'subscriptions_only': frozenset(('subscriptions', 'feed_posts')),
    'subscribers_only': frozenset(('subscribers', 'feed_posts')),
}

assert len(SLOT_PATTERN) == DISCOVERY_EVERY_N_SLOTS
assert sum(1 for s in SLOT_PATTERN if s == 'discovery') == 1
assert sum(1 for s in SLOT_PATTERN if s == 'feed_posts') == 1
