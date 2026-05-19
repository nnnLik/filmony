# Feature: Catalog Search Providers (`catalog-search-providers`)

## Summary

**Shipped:** Search-first, **local-first** catalog for **films (Kinopoisk)** and **games (RAWG)**. Users query by title (minimum length enforced client- and server-side, **provider-specific**) before creating a user card. Matching prefers rows already persisted as `Film` / `Game`; gaps are filled via provider list APIs with controlled outbound traffic (**~800 ms** debounced UI, **`AbortSignal`** cancellation for superseded queries, server-side **in-process TTL coalescing** for list queries ~45s per key).

## Status

**Completed** for the scoped delivery (see `.cursor/active/catalog-search-providers/result.md` for verification log).

## Behavior

### Data

- **`game` table / `Game` model:** RAWG identity (`rawg_id` unique), display fields, JSON list/detail snapshots, sync timestamps.
- **`catalog_item`:** `CatalogProvider` includes `rawg`; nullable `game_id` (CASCADE) alongside existing `film_id`. Provider-backed rows reference **exactly one** of `film_id` or `game_id`. `(provider, external_id)` unique. `no_provider` remains for **manual** cards only — not used for catalog search hits.

### Services

- **RAWG:** `SearchRawgCatalogGamesService` — local ILIKE on `Game`, then RAWG `search_games` when needed; upserts from list/detail DTOs; `EnsureRawgCatalogItemService` links `CatalogItem` idempotently. **Live RAWG JSON** may return list-shaped blobs for fields such as **`ratings`**, `added_by_status`, and `reactions`; the OpenAPI DTO layer accepts object-or-array shapes so parsing does not fail when the API returns arrays.
- **Kinopoisk:** `SearchKinopoiskFilmsLocalFirstService` — local `Film` ILIKE on first page; optional `search_films_by_keyword` merge; upserts `Film` + `CatalogItem`.
- **Resolve:** `ResolveCatalogItemService` / `POST /api/catalog/resolve` unchanged in role: **Kinopoisk URL → film catalog item** (still supported).

### HTTP API

```http
GET /api/catalog/search?provider=kinopoisk&q=<query>&page=<n>&limit=<m>
GET /api/catalog/search?provider=rawg&q=<query>&page=<n>&limit=<m>
```

- **Auth:** required (`CurrentUser`).
- **`q`:** trimmed; minimum length depends on **`provider`**: **Kinopoisk ≥ 3** characters, **RAWG ≥ 4** → otherwise **422** with a clear message.
- **`page`:** ≥ 1; **`limit`:** 1–40, default **15** (response may slice Kinopoisk hits to `limit`).
- **Response:** `{ "items": [ { "provider", "external_id", "kind": "film"|"game", "title", "subtitle", "cover_url", "catalog_item_id", "source": "local"|"remote" } ], "has_more": bool }`. Kinopoisk provider-sourced hits use `source="remote"` (mapped from internal provider source).
- **Errors:** provider transport failures → **502**.

`POST /api/catalog/resolve` remains for URL-based Kinopoisk resolution (non-goal to remove in this slice).

### Frontend

- **`CreateCardPage`:** Choose **film / game / manual** → film and game paths call **`GET /api/catalog/search`** via `catalogApi` with **~800 ms** debounce, **per-provider** minimum length before issuing a request (**≥ 3** film, **≥ 4** game), and **`AbortSignal`** support so in-flight requests are cancelled when the query changes. Infinite scroll / “load more” where implemented. Optional **Kinopoisk URL** block for film mode. Manual path keeps `no_provider` authoring.

## Tests

- **API:** `backend/src/tests/api/test_catalog_routes.py` — resolve + search (local-only, remote monkeypatched, validation, `no_provider` rejected on search, RAWG short-query 422).
- **Providers / DTO:** `backend/src/tests/providers/test_rawg_openapi_dto_ratings_blob.py` — list-shaped `ratings` / related fields on list and detail payloads.
- **Services:** `backend/src/tests/services/test_search_rawg_catalog_games_service.py`, `backend/src/tests/services/catalog/test_search_kinopoisk_films_local_first.py`, `backend/src/tests/services/catalog/test_ttl_coalescing_cache.py`.
- **Models:** `backend/src/tests/models/test_game_catalog_schema.py`.

**Runner:** Docker — `docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend pytest` (full suite includes these; see `result.md` for last recorded counts).

**Frontend:** `cd frontend && npm run lint && npm run build`.

## Configuration

- **`RAWG_API_KEY`** — required by `RawgSettings` at process startup (see `vars/.env.example`). Local/dev must define it; CI/tests should pass a dummy key (e.g. `RAWG_API_KEY=test`) when invoking pytest inside Docker if the compose env omits it.

## Non-goals (this slice)

- Removing `POST /api/catalog/resolve`.
- Dedicated **public game detail** pages beyond what create-card search needs.
- Merging external **genres/tags** into user tag chips automatically.
- Distributed Redis cache / multi-instance **search** deduplication (in-process coalescing only for now).

## Known limitations

- Kinopoisk **URL resolve** remains for paste flows; search-first is additive.
- No standalone game detail route focused on community/catalog parity with films.
- **Provider genres** are catalog/display metadata, not user tags.

## References

- `.cursor/features/catalog-search-providers/feature.md`
- `.cursor/active/catalog-search-providers/plan.md`
- Read-only blueprint: `.cursor/plans/catalog-search-providers_4b034044.plan.md` (do not edit for progress logging)
- **v2 / legacy naming cleanup roadmap:** [`docs/features/catalog-search-providers-compat-cleanup-map.md`](catalog-search-providers-compat-cleanup-map.md)
- Universal cards: [`docs/features/abstract-user-cards.md`](abstract-user-cards.md)
