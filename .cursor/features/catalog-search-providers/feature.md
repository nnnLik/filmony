# Feature Request: Catalog Search Providers (`catalog-search-providers`)

## Metadata
- Feature slug: `catalog-search-providers`
- Author: (team / planning)
- Created at: 2026-05-14
- Priority: high (core create flow)
- Target area: fullstack

## Problem
- Card creation today leans on **Kinopoisk URL paste** (`POST /api/catalog/resolve`). Users need a **consistent, search-first** path for films and games: type a title, pick a hit, persist the choice.
- Without **local-first** behavior, repeated searches burn provider quotas and add latency even when titles already live in our DB.

## Scope
- In scope:
  - **Local-first catalog search**: query local films/games first; call Kinopoisk (films) or RAWG (games) when results are insufficient; **upsert subject + `catalog_item`** for provider hits surfaced to the user.
  - **`Game` table**, `CatalogProvider.rawg`, `CatalogItem.game_id`, migrations + model/schema tests as needed.
  - **Kinopoisk text search** (`/api/v2.1/films/search-by-keyword`) in transport layer; detail fetch unchanged endpoint family.
  - **`GET /api/catalog/search`** with normalized `provider` + `q` + pagination; pytest coverage for routing and merge/dedupe behavior.
  - **Create-card UI**: type/provider-aware search-first wizard with **manual `no_provider` fallback** preserved.
  - Backend caching/throttling knobs (debounce frontend; backend cache 5–15 min; Kinopoisk search rate discipline).
- Out of scope (this slice):
  - Removing **`POST /api/catalog/resolve`** (may remain during transition).
  - Public game detail pages unless strictly required by create flow.
  - Merging provider genres into user tags; shelf/category as catalog identity keys.

## Functional Requirements
- [ ] Extend catalog model so games are first-class (**`game`**, **`catalog_item.game_id`**, **`CatalogProvider.rawg`**); enforce exactly one subject for provider-backed catalog items in services.
- [ ] **RAWG**: local game search → RAWG **`search_games`** / **`get_game`** fallback; **`UpsertRawgGameService`** preserves detail fields on list-only updates; list/detail snapshots stored.
- [ ] **Kinopoisk**: local film search → keyword search fallback; persist merged catalog rows appropriately.
- [ ] **`GET /api/catalog/search`** returns **`CatalogSearchHitDTO`-shaped** JSON (`kind`, `source: local | provider`, `catalog_item_id` when known, deduped **`(provider, external_id)`**).
- [ ] **Create UI** uses search API for films (Kinopoisk) and games (RAWG), with poster/title/year metadata and empty-state → manual path.

## Acceptance Criteria
- [ ] Local hits return **without** outbound provider calls when the catalog/game tables already satisfy the query.
- [ ] Provider fallback **upserts** `Film`/`Game` and **`catalog_item`** so selecting a hit can drive **`catalog_item_id`** / external identity on **`POST /api/cards`** (aligned with universal card contracts).
- [ ] API tests prove local-first paths, RAWG persistence, Kinopoisk search integration points, dedupe merge, and card-create compatibility for a RAWG-selected row.
- [ ] Frontend **`npm run lint && npm run build`** clean after search-first UX changes.

## Constraints
- Technical: Prefer **Docker** for `make backend-test` / ruff runs; RAWG/Kinopoisk keys and quotas in env/settings.
- Product: **API economy**: min query length (~2–3 chars), frontend debounce **400–500 ms**, backend normalized-query cache **5–15 min**, Kinopoisk search **≤ 5 req/s** where applicable.

## References
- Read-only snapshot: `.cursor/plans/catalog-search-providers_4b034044.plan.md` (do not mutate as part of implementation notes).
- Related product doc: universal cards (`docs/features/abstract-user-cards.md` — `provider`, `catalog_item`, create paths).
- Code touchpoints (expected): `backend/src/models/catalog_item.py`, new `backend/src/models/game.py`, `backend/src/services/catalog/`, `backend/src/providers/rawg/`, `backend/src/providers/kinopoisk/`, `backend/src/api/catalog/routes.py`, `frontend/src/pages/CreateCardPage.tsx`, `frontend/src/api/catalogApi.ts`.
