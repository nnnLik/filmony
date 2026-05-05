# 007 — Feed (friends + “вкидки”)

## Metadata

| Field | Value |
|--------|--------|
| **Feature slug** | `feed-friends-and-stranger-inserts` |
| **Priority** | P1 |
| **Target area** | fullstack |
| **Depends on** | [001](./001-telegram-user-base.md), [003](./003-friends-requests-and-list.md), [005](./005-movie-rating-with-tags.md), [008](./008-doppelganger-recommendations.md) partial for stranger selection |
| **Unlocks** | Primary discovery surface for the app |

## Summary

Build the **main feed**: predominantly **friends’ new movie cards**, interleaved with occasional **“вкидки”** — cards from **non-friend users** who match the viewer’s taste profile (mood/tag affinity per product rules). Support sorting by **date** and by **personal fit** ([`.cursor/user-story.md`](../user-story.md)). Use **Redis-cached** feed segments with TTL as in [`.cursor/tech.md`](../tech.md) §6–7.

## Problem

Users need a single stream to discover what friends watched and serendipitously see aligned strangers’ picks—without polluting the feed with noise.

## Backend

### Responsibilities

- **Compose feed**: query friends’ recent cards + sample stranger inserts from candidate pool (users with similarity above threshold from **008** / Redis vectors).
- **Sorting**: `recent` (created_at desc); `for_you` — score from similarity + recency decay (define formula in implementation plan).
- **Pagination**: cursor-based for stable infinite scroll.
- **Cache**: precomputed feed per user in Redis with invalidation on new friend card / configurable TTL (5 min–1 h per tech doc).
- **SSE** (from stack table): optional channel for “new items” push to Mini App—phase 2 if not MVP.

### API (planned)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/api/feed` | Query: `sort`, `cursor`, `limit` → items with card + film + author summary |

### Data joining

- Each item: `movie_card` + `film` poster/title + `user` display + friendship hint (`is_friend` boolean).

### Celery

- Periodic or event-driven **feed rebuild** jobs; invalidate on new card from friend or on similarity graph update.

### Existing codebase references

| File | Note |
|------|------|
| [`backend/src/conf/settings.py`](../../backend/src/conf/settings.py) | Feed page size defaults, cache TTL env vars |

### Suggested new modules

- `backend/src/services/feed_service.py`
- `backend/src/api/feed/routes.py`

## Frontend

### Responsibilities

- **Feed home**: infinite scroll, pull-to-refresh if Telegram UI supports pattern.
- **Sort selector**: “По дате” / “Как тебе зайдёт” (labels per copy deck).
- **Card teaser**: poster, title, author, rating snippet, mood tags abbreviated.
- Tap → card detail (**006**/**005**).

### Real-time

- If SSE is implemented: subscribe on mount, merge new items at top with dedupe.

### Suggested new files

- `frontend/src/pages/FeedPage.tsx`
- `frontend/src/components/feed/FeedItem.tsx`, `FeedSortControl.tsx`

## Acceptance criteria

- [ ] Authenticated user sees friends’ cards after friendships and cards exist.
- [ ] Stranger inserts appear at configured rate/frequency and only when similarity data exists; otherwise feed is friends-only without errors.
- [ ] Sort modes return deterministic ordering for same cursor semantics (document cursor contract).
- [ ] Cached responses invalidated within acceptable staleness window per env TTL.

## Out of scope

- Full TikTok-style ranking ML; start with rule-based score from **008** vectors.
- Global public timeline for all users.

## References

- [`.cursor/tech.md`](../tech.md) — §4 (лента), §6 (кеш), SSE row in stack table.
- [`.cursor/user-story.md`](../user-story.md) — Способ 1, сортировки.
- [003](./003-friends-requests-and-list.md), [005](./005-movie-rating-with-tags.md), [008](./008-doppelganger-recommendations.md)
