# Result: catalog-search-providers

## Status
`completed` (feature surface shipped; see risks below)

## What was implemented

- **Schema:** `Game` model/table (RAWG-aligned, JSON snapshots, sync timestamps); `CatalogProvider.rawg`; nullable `catalog_item.game_id` with FK to `game.id`; uniqueness on `(provider, external_id)` preserved. Migration `p3q4r5s6t890_game_rawg_catalog.py`.
- **RAWG:** List/detail DTO merge (`rawg_game_snapshot_utils`), upsert services, `EnsureRawgCatalogItemService`, `SearchRawgCatalogGamesService` (local ILIKE first → RAWG `search_games` fallback; dedupe; persists games + catalog items). In-process **TTL coalescing** for outbound list queries (`ttl_coalescing_cache`, ~45s).
- **Kinopoisk:** `KinopoiskProviderTransport.search_films_by_keyword`; `SearchKinopoiskFilmsLocalFirstService` (local `Film` ILIKE on page 1, optional remote merge; upserts `Film` + `CatalogItem`); Kinopoisk search uses same coalescing pattern.
- **API:** `GET /api/catalog/search` — `provider=kinopoisk|rawg`, trimmed **`q`** with provider-specific minimum length (**≥ 3** Kinopoisk, **≥ 4** RAWG → else **422**), `page` ≥ 1, `limit` 1–40 (default 15). Response: `items[]` with `kind`, `source` (`local`|`remote`; Kinopoisk maps provider → `remote`), `catalog_item_id`, titles/cover. Transport failures → **502**. `POST /api/catalog/resolve` **retained** for Kinopoisk URL flows.
- **RAWG live JSON compatibility:** search/detail DTOs tolerate list-shaped blobs for **`ratings`** and related keys (`added_by_status`, `reactions`) instead of strict object maps, avoiding parse errors that bubbled as **502** on catalog search.
- **Search traffic shaping:** create-card catalog client uses **~800 ms** debounce, **per-provider** minimum string length before calling the API (aligned with backend), and **`AbortSignal`** so superseded keystrokes cancel in-flight fetches (React Query).
- **Frontend:** `CreateCardPage` — step “what to add” → film (Kinopoisk search + optional URL block), game (RAWG search), or manual (`no_provider`); `catalogApi.searchCatalog`, debounce, infinite query / “load more”; game path submits with `catalog_item_id` and display fields.
- **Tests:** `test_catalog_routes.py` (search + resolve branches), `test_search_rawg_catalog_games_service.py`, `test_rawg_openapi_dto_ratings_blob.py`, `test_search_kinopoisk_films_local_first.py`, `test_game_catalog_schema.py`, `test_ttl_coalescing_cache.py`, etc.

## Changed files (primary)

- Backend: `backend/src/models/game.py`, `catalog_item.py`, `__init__.py`; `migrations/versions/p3q4r5s6t890_*`; `api/catalog/routes.py`, `schemas.py`; `providers/rawg/*`, `providers/kinopoisk/*`; `services/catalog/*` (search, ensure, upsert, cache, resolve); `conf/settings.py` (`RawgSettings` / `RAWG_API_KEY`); tests under `src/tests/api/test_catalog_routes.py`, `src/tests/providers/test_rawg_openapi_dto_ratings_blob.py`, `src/tests/services/catalog/`, `src/tests/services/test_search_rawg_catalog_games_service.py`, `src/tests/models/test_game_catalog_schema.py`.
- Frontend: `frontend/src/pages/CreateCardPage.tsx`, `api/catalogApi.ts`, `components/cards/CardCategoryChip.tsx`, `lib/openExternalUrl.ts` (and related profile/card API touches on branch).
- Config: `vars/.env.example` (`RAWG_API_KEY`, `RAWG_API_BASE_URL`).

## Verification steps and outcomes

| Check | Command | Result |
| --- | --- | --- |
| Backend full suite | `docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend pytest -q` | **267 passed** *2026-05-14 card-first rename pass* |
| RAWG DTO + catalog search slice | `docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend pytest src/tests/providers/test_rawg_openapi_dto_ratings_blob.py src/tests/api/test_catalog_routes.py src/tests/services/test_search_rawg_catalog_games_service.py -v` | **20 passed** (~4s) *2026-05-15 final pass* |
| Catalog slice (broader) | Same Docker env, paths: `src/tests/api/test_catalog_routes.py` `src/tests/services/catalog/` `src/tests/services/test_search_rawg_catalog_games_service.py` `src/tests/models/test_game_catalog_schema.py` | **22 passed** *earlier recorded* |
| Frontend | `cd frontend && npm run lint && npm run build` | **Pass** *2026-05-15 final pass* |
| Ruff | `make backend-lint` | **Pass** *2026-05-15 final pass* |
| Host cache cleanup | `find backend/src -type d -name __pycache__ -exec rm -rf {} +` (optional `.pytest_cache`/`.ruff_cache`) | Done before focused pytest |
| Cards API tests | `docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend pytest src/tests/api/test_cards_routes.py` | **53 passed** *earlier recorded* |

## Known limitations and next steps

- **Legacy naming (intentional):** DB tables/constraints (`movie_card`, `movie_card_comment`), polymorphic reaction/export identifiers (`movie_card`, `movie_card_comment`), several HTTP JSON keys (`movie_card_id`, `film_*`, `referenced_movie_cards`), media subdirectory `movie_card_comments`, RAWG OpenAPI `movies_count`, and Celery task registry names (`tasks.telegram_engagement.notify_movie_card_*`, `deliver_shared_movie_card`) remain for persistence and client/worker compatibility; internals use card-first symbols where refactored.

- **`POST /api/catalog/resolve` (Kinopoisk URL)** kept for legacy / paste flows; search-first is the primary create path for films.
- **No dedicated public game detail page** in-app; games are discoverable via search and card UX.
- **Provider metadata (e.g. genres from RAWG/Kinopoisk)** is not auto-mapped into **user custom tags**; user tags remain user-controlled.
- **Caching:** in-process TTL coalescing reduces duplicate outbound list calls per worker; **distributed (Redis) cache / stricter Kinopoisk search rate limits** remain optional hardening for multi-instance or high-burst traffic.
- **Ops:** ensure `RAWG_API_KEY` is set wherever the app starts (not only `RAWG_API_TOKEN`); tests should inject `RAWG_API_KEY=test` if env files omit it.

## Risks

- **RAWG response drift:** additional fields flipping between object/list shapes could still require DTO tweaks; current coverage targets `ratings`/`added_by_status`/`reactions` list cases.
- **Shared `filmony_test` DB:** rare DDL oddities (e.g. orphaned types) if tests are interrupted; re-run or reset schema if `create_all` fails spuriously.
