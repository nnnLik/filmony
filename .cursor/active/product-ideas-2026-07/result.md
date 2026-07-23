# Filmony Product Ideas Backlog (2026-07)

Research grounded in shipped code and docs. **Ranked** by impact × leverage on existing modules.  
**15 ideas** — mix of quick wins (S), medium (M), ambitious (L). Already-planned specs are noted, not re-proposed as net-new.

---

## Top 5 — Why Now

| Rank | Idea | Why now |
|------|------|---------|
| **1** | Feed explainability labels | Global feed (`docs/features/global-feed-tabs-timeline-sse.md`) dropped recommendation modes; users see a flat timeline without knowing *why* an item surfaced. Backend already emits `feed_source` on legacy feed and merge layer exists in `backend/src/const/feed.py` — UI labels are the missing trust layer. Spec: `.cursor/features/feed-explainability-export-offline/`. |
| **2** | Game / catalog community pages | RAWG search and game-backed cards shipped (`docs/features/catalog-search-providers.md`, `abstract-user-cards.md`), but only films have `/films/:id` + `GET /api/films/{id}/community-cards`. Games lack parity — creates a visible product hole as users add non-film cards. |
| **3** | Mutual watchlist overlap | `watchlist-cards` + `watch_with_user_ids` + subscriptions + Telegram invites are live. Surfacing "3 people you follow also have this in «Позже»" turns passive lists into social discovery without new graph primitives. |
| **4** | Weighted taste match (v2) | Profile stats v1 ships Jaccard peers (`docs/features/profile-analytics-redesign.md`); product spec is written and blocked only on decisions (`.cursor/features/profile-taste-match/`). Natural follow-up while analytics tab is fresh. |
| **5** | Co-view coordination | Watchlist already stores `watch_with_user_ids`, sends Telegram pushes (`send_watchlist_invite_notification.py`), and creates planned cards. Missing piece: a lightweight "session" view — who accepted, nudge to rate after watching — fits Telegram mini-app rituals. |

---

## Ranked Ideas

### 1. Feed explainability labels
- **Problem:** Users don't trust or understand items in the feed; global timeline feels random.
- **Why Filmony:** Recommendation merge already tags sources (`subscriptions`, `personal_affinity`, `discovery`, etc.) in `list_movie_card_feed` / feed DTOs; product copy can mirror Telegram-native language ("Из подписок", "Похоже на ваши теги").
- **Complexity:** **S**
- **Dependencies:** `backend/src/services/cards/list_movie_card_feed.py`, `backend/src/const/feed.py`, `FeedPage` / feed item components, spec `.cursor/features/feed-explainability-export-offline/`
- **Note:** Partial overlap with planned spec — treat as highest-priority slice (labels only).

### 2. Offline-first feed snapshot (client cache)
- **Problem:** Telegram WebView + flaky mobile network → blank feed on reopen.
- **Why Filmony:** Feed already paginates with stable cursors; `scroll-restore` and `FeedCardGlobalAudioProvider` show client-side persistence patterns exist.
- **Complexity:** **S**
- **Dependencies:** `FeedPage`, React Query cache or IndexedDB, user-scoped cache key on session; spec `.cursor/features/feed-explainability-export-offline/` §C
- **Note:** No backend work; pairs with global feed SSE ("данные от …").

### 3. JSON export of my cards (in-app download)
- **Problem:** CSV export via Telegram bot (`docs/features/profile-csv-export.md`) doesn't suit users who want JSON for scripts/backups inside the mini-app.
- **Why Filmony:** `ExportMyUserCardsCsvTelegramService` / card list queries already aggregate all fields; JSON is a second serializer on the same service layer.
- **Complexity:** **S**
- **Dependencies:** `backend/src/services/profile/export_my_user_cards_csv_telegram.py`, `ProfilePage`, spec `.cursor/features/feed-explainability-export-offline/` §B

### 4. Reaction-added Telegram notifications
- **Problem:** Custom reactions are expressive but silent outside the app; authors miss engagement.
- **Why Filmony:** `notify_reaction_added.py` hook stubbed; Celery + engagement delivery (`telegram/engagement_delivery.py`) and reaction toggle API are shipped (`docs/features/movie-card-custom-reactions.md`).
- **Complexity:** **S**
- **Dependencies:** `SetOrToggleUserReactionService`, `tasks/telegram_engagement.py`, rate-limit rules to avoid spam

### 5. «Друзья оценили» on film/game community pages
- **Problem:** Community title pages show strangers' cards but not *your subscriptions'* ratings at a glance.
- **Why Filmony:** `GET /api/cards/{id}/following-ratings` and `list_film_community_cards` exist; same join logic applies per `film_id` or `catalog_item_id`.
- **Complexity:** **S**
- **Dependencies:** `FilmDetailPage`, future game detail page, `list_following_ratings_for_user_card.py`, `docs/features/film-catalog-community-view.md`

### 6. Game / unified catalog community detail page
- **Problem:** Game cards resolve via RAWG but there's no `/games/:id` (or catalog slug page) with synopsis + community ratings like films.
- **Why Filmony:** Asymmetric UX blocks the "universal cards" narrative (`abstract-user-cards.md`); `Game` model + `catalog_item.game_id` + community list pattern already proven for films.
- **Complexity:** **M**
- **Dependencies:** `backend/src/models/game.py`, `list_film_community_cards.py` (generalize to catalog_item), `SearchPage` / card create flows, new `CatalogDetailPage` or `/catalog/:id`

### 7. Mutual watchlist overlap widget
- **Problem:** «Позже» lists are solo by default; users don't see shared intent with people they follow.
- **Why Filmony:** `watchlist_entry` keyed by user + card/catalog; subscriptions graph is the filter; no new social primitive needed.
- **Complexity:** **M**
- **Dependencies:** `backend/src/services/watchlist/`, `list_user_subscriptions.py`, `FilmDetailPage`, card detail, profile watchlist grid

### 8. Co-view session & post-watch nudge
- **Problem:** «Смотрим вместе» invites fire Telegram pushes but there's no shared status ("who's in", "everyone watched?") or prompt to rate together.
- **Why Filmony:** `watch_with_user_ids`, planned cards (`is_planned`), and watchlist→rate flow (`GET /api/me/planned-card`) are implemented; Telegram is the natural coordination surface.
- **Complexity:** **M**
- **Dependencies:** `create_watchlist_entry_*`, `send_watchlist_invite_notification.py`, `CreateCardPage` prefill, optional lightweight `watch_session` table or status on entries

### 9. Weighted profile taste match (v2)
- **Problem:** Jaccard on shared `film_id` ignores tags, rating agreement, games, favorites — peers feel arbitrary.
- **Why Filmony:** Stats tab already shows `taste_peers[]`; full spec with signal catalog exists; extends `get_user_profile_social_insights.py` without ML.
- **Complexity:** **M** (decisions) → **L** (full breakdown UI)
- **Dependencies:** `.cursor/features/profile-taste-match/`, `ProfileStatsCharts.tsx`, card tags/genres/favorites models
- **Note:** Already planned — rank high because infra and v1 UI exist.

### 10. «Following» filter on global feed (hybrid tab)
- **Problem:** Global feed MVP is fully public; users with subscriptions may want a **people I follow** slice without returning to legacy recommendation feed.
- **Why Filmony:** `GET /api/cards/feed?mode=subscriptions_only` and global `GET /api/feed/global?kind=` can coexist; SSE head applies to both.
- **Complexity:** **M**
- **Dependencies:** `global-feed-tabs-timeline-sse`, `list_global_feed.py`, subscription id sets from `list_following_user_ids_for_follower_user.py`

### 11. Monthly recap + shareable Telegram card
- **Problem:** No reflective moment to revisit activity or share taste identity outside the app.
- **Why Filmony:** Profile stats, heatmap, top tags, favorites, watchlist churn — all queryable; Telegram share aligns with mini-app distribution.
- **Complexity:** **M**
- **Dependencies:** `.cursor/features/monthly-recap-shareable-summary/`, `get_user_card_stats.py`, `mini_app_link.py`, optional Celery monthly job

### 12. YouTube (and video) card source
- **Problem:** Users consume YouTube reviews/essays; only Kinopoisk/RAWG/manual paths exist today.
- **Why Filmony:** Abstract cards (`provider`, `display_*`, `source_url`) and resolve-by-url pipeline ready; oEmbed avoids API keys.
- **Complexity:** **M**
- **Dependencies:** `.cursor/features/youtube-card-source/`, `ResolveCatalogByUrlService`, `CreateCardPage`, `WatchlistForm`

### 13. Shelf discovery on public profiles
- **Problem:** Categories/shelves organize *your* library but visitors can't browse another user's shelves as taste chapters.
- **Why Filmony:** `user_card_category` + profile filter `?category_id=` exist for owner; public list API partially there (`list_public_user_card_categories.py`).
- **Complexity:** **M**
- **Dependencies:** `abstract-user-cards.md` roadmap, `PublicProfilePage`, `GET /api/users/{id}/cards`

### 14. Doppelgänger layer for `personal_affinity`
- **Problem:** MVP affinity is genre/tag overlap only; "вкидки" from taste-neighbors were core product vision (`.cursor/user-story.md`).
- **Why Filmony:** Feed engine slot for `personal_affinity` and Redis/Celery infra exist (`docs/features/celery-redis-workers.md`); 008 spec defines 60/40 rating+tag similarity.
- **Complexity:** **L**
- **Dependencies:** `.cursor/features/008-doppelganger-recommendations.md`, `feed-recommendation-engine.md`, Redis neighbor cache, incremental recompute jobs

### 15. Search: "people who rated this title"
- **Problem:** Finding friends' takes on a title requires opening community page or a specific card.
- **Why Filmony:** `search_user_suggestions.py` already computes mutual circle; catalog search returns `catalog_item_id`; following-ratings query is the join.
- **Complexity:** **M**
- **Dependencies:** `SearchPage`, `search_catalog_cards.py`, subscriptions filter, optional new `GET /api/catalog/{id}/following-cards`

---

## Honorable mentions (lower priority / narrower)

| Idea | Size | Rationale |
|------|------|-----------|
| Public shelf browse API hardening | S | Security/visibility rules before UI shelf tabs on `/u/:slug` |
| Feed bookmark / save for later | M | Favorites exist on owned cards, not on feed posts or others' cards |
| Comment thread follow (notify without @) | M | Reply notifications exist; explicit thread subscription is new model |
| Audio vibe discovery strip | S | `audio-vibe-cards` playback works; no browse-by-audio feed facet |
| Production readiness gate | P0 infra | `.cursor/features/production-readiness/` — not a user feature but blocks launch |

---

## Explicitly not proposed (shipped or cancelled)

- Friend requests graph — **cancelled**; use subscriptions (`003-friends-requests-and-list.md`).
- Legacy friends-only feed — **superseded** by feed engine + global feed.
- Basic comments, reactions, watchlist, subscriptions, Kinopoisk resolve, profile stats v1, Telegram digests, CSV export — **done** (see `docs/features/`).

---

## Suggested next actions

1. **Quick win bundle:** #1 + #2 + #4 (explainability, offline cache, reaction notifications) — mostly frontend + thin API fields.
2. **Parity sprint:** #6 + #5 (game community page + following ratings widget).
3. **Social depth:** #7 + #8 (watchlist overlap + co-view) — leverages watchlist-cards investment.
4. **Unlock planned specs:** Resolve `profile-taste-match` decisions doc, then implement #9.

---

## Artifact

- **Primary:** `.cursor/active/product-ideas-2026-07/result.md`
- **Index:** `docs/features/product-ideas-backlog.md`
- **Research date:** 2026-07-23
