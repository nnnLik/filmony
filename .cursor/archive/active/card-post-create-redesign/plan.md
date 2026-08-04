# Card / Post Create Redesign Plan

## Feature
- Slug: card-post-create-redesign
- Status: in_progress
- Spec: [docs/superpowers/specs/2026-07-19-card-post-create-redesign-design.md](../../../docs/superpowers/specs/2026-07-19-card-post-create-redesign-design.md)
- Full plan copy: [docs/superpowers/plans/2026-07-19-card-post-create-redesign.md](../../../docs/superpowers/plans/2026-07-19-card-post-create-redesign.md)

## Goal

Make create flows from the feed obvious (≤2 taps to choose card/post/later), keep `UserCard` abstract, and fill fields via Sources→Candidates plus cover upload/paste — without YouTube or renaming `movie_card`.

## Architecture

Backend adds a candidates coordinator over existing Kinopoisk/RAWG search, URL resolve by host, and cover upload mirroring feed-post images. Frontend replaces dual feed icons with a Create action sheet, rewrites `/cards/new` to smart field + one scroll form, and moves watchlist create to `/watchlist/new`. Existing `POST /api/cards`, `POST /api/feed-posts`, `POST /api/me/watchlist` stay the write path.

**Tech stack:** FastAPI services (`build`/`execute`), pytest in Docker; React + Telegram UI + React Query; RustFS upload via existing image service.

## Global constraints

- Card remains abstract: `display_*` + optional `catalog_item_id`; providers are Sources, not card types.
- No film vs game title dedup on server; Castlevania = two rows; user picks.
- `kind_hint` / `kind` are UI-only; never sent as card type on create.
- Watchlist create only via `/watchlist/new` (not `?mode=watchlist` on `/cards/new`).
- YouTube out of scope; no `movie_card` rename; no merged post+card compose.
- Docker-first backend tests: `make backend-test` / `make backend-test-one`.
- Frontend gate: `cd frontend && npm run lint && npm run build`.

## Task sequence

### Task 1 — Delivery scaffolding + plan copy
Create feature slug artifacts and copy plan into `docs/superpowers/plans/` and `.cursor/active/.../plan.md`. Log planning action.

### Task 2 — `SearchCatalogCandidatesService` + `GET /api/catalog/candidates`
- DTO fields per spec: `candidate_id`, `provider`, `external_id`, `kind`, `kind_hint?`, `title`, `subtitle`, `cover_url`, `catalog_item_id`, `source`, `degraded?`
- Response: `{ items, has_more, meta: { degraded_sources } }`
- Parallel Kinopoisk + RAWG; merge; sort local before remote; dedup only same `provider+external_id`
- On one source failure: still 200, populate `meta.degraded_sources`
- TDD in Docker; `candidate_id` = `"{provider}:{external_id}"`

### Task 3 — `ResolveCatalogByUrlService` + `POST /api/catalog/resolve-by-url`
- Body `{ url }`; v1 hosts only `kinopoisk.ru` / `www.kinopoisk.ru`
- Unknown host → 422; not found → 404
- Keep legacy `POST /api/catalog/resolve` for compat

### Task 4 — Cover upload `POST /api/cards/covers/upload`
- Multipart `file` → `{ url }` under cards media proxy pattern
- Extend `UploadFeedPostImageService` with `user_card_covers` subdir (JPEG/PNG/WebP/GIF, 5MB)

### Task 5 — Frontend API + hooks
- Wire `searchCatalogCandidates`, `resolveCatalogByUrl`, `uploadUserCardCover`
- Hooks: debounced text → candidates; immediate URL → resolve-by-url

### Task 6 — Feed `CreateActionSheet`
- Replace `+` and pen with labeled «Создать»
- Sheet rows: Карточка → `/cards/new`; Пост → `openCompose()`; Позже → `/watchlist/new`

### Task 7 — Rewrite `CreateCardPage` Screen A (smart field)
- Remove film/game/manual picker and step progress
- Smart field + `CatalogCandidatesList`; tap candidate or «Создать вручную» → Screen B
- Preserve bootstrap: `filmId`, `fromCard`+`intent=rate`

### Task 8 — Screen B scroll form + `CardCoverBlock`
- Single scroll: title, summary, cover, rating, company/moods, shelf, tags, note, publish
- Submit via existing `createMovieCard`; success → `/cards/:id`
- Share + audio as post-success secondary

### Task 9 — `CreateWatchlistPage` + deep-link migration
- New page + route `/watchlist/new`; shared `WatchlistForm`
- Retarget `FilmDetailPage` and `WatchlistPosterGrid` links
- Remove watchlist branch from `CreateCardPage`

### Task 10 — Verification + feature docs closeout
- `make backend-test`; frontend lint/build
- Manual QA checklist from spec
- Write `docs/features/card-post-create-redesign.md`, `result.md`, action-log
