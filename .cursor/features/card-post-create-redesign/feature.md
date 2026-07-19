# Card / Post Create Redesign

## Scope

Redesign create flows from the feed so users can choose card, post, or watchlist in ≤2 taps, replace the 4-step `CreateCardPage` wizard with a smart search field and single scroll form, and move watchlist create to a dedicated `/watchlist/new` page.

**Delivery goals (Approach 2, approved spec):**

- **≤2 meaningful taps** from feed to clear choice: card / post / later.
- **One smart field** «название или ссылка» with mixed catalog candidates instead of provider picker on step 1.
- **One long scroll form** after candidate pick or manual entry — no multi-step wizard.
- **Cover always with preview** and three equal actions: Upload / Link / Buffer.
- **Architecture:** `UserCard` stays abstract (`display_*` + optional `catalog_item_id`); Kinopoisk, RAWG, and future integrations are **Sources**, not card types.
- **Thin backend:** Sources→Candidates API + cover upload; existing `POST /api/cards`, `POST /api/feed-posts`, `POST /api/me/watchlist` write paths change minimally.

**In scope:**

- Backend: `GET /api/catalog/candidates`, `POST /api/catalog/resolve-by-url`, `POST /api/cards/covers/upload`.
- Frontend: Feed `CreateActionSheet`, rewrite `CreateCardPage` (Screen A + B), new `CreateWatchlistPage`, API clients and hooks.
- Deep-link migration for watchlist callers to `/watchlist/new`.

**Non-goals:**

- YouTube Source and any new providers in this delivery.
- Renaming `movie_card` / legacy API names in code and DB.
- Merged post+card compose in one screen.
- Multi-step wizard for rated card or watchlist.
- Watchlist branch inside rated scroll form.
- Feed visual redesign, localStorage drafts, duplicate-card semantics change.

**Spec source of truth:** `docs/superpowers/specs/2026-07-19-card-post-create-redesign-design.md`

## Acceptance Criteria

### Backend (pytest inside Docker)

- `GET /api/catalog/candidates`: happy path merge Kinopoisk+RAWG; empty query; pagination; partial response when one Source fails; no over-dedup of film+game with same title (Castlevania = two rows).
- `POST /api/catalog/resolve-by-url`: Kinopoisk URL happy path; unknown host → 422; not found → 404.
- `POST /api/cards/covers/upload`: success; oversize → 413; bad MIME → 400.
- Regression: `POST /api/cards` with `catalog_item_id` and manual `no_provider` paths unchanged.
- Watchlist create from new page still creates entry + feed post.

### Frontend

- `cd frontend && npm run lint && npm run build` — zero errors in touched files.
- Feed → «Создать» → action sheet with Карточка / Пост / Позже.
- Feed → Карточка → smart field within ≤2 taps.
- Paste Kinopoisk URL → resolve → scroll form with cover preview.
- Castlevania search → two candidate rows → user picks game → correct provider on save.
- Cover: upload, link, and buffer each update preview.
- Duplicate card warning still appears.
- Feed → Пост → `FeedComposeSheet` opens.
- Feed → Позже → short watchlist form on `/watchlist/new`, no rating slider.
- Success after card create → navigate to `/cards/:id`.
