# Implementation Plan

## Feature
- Slug: `catalog-search-providers`
- Source spec: `.cursor/features/catalog-search-providers/feature.md`
- Architecture snapshot (read-only, do not edit): `.cursor/plans/catalog-search-providers_4b034044.plan.md`

## Goal
Deliver a **search-first, local-first** catalog pipeline for **films (Kinopoisk)** and **games (RAWG)**: unified **`GET /api/catalog/search`**, persisted provider subjects (`Film`/`Game`), idempotent **`CatalogItem`** rows (`(provider, external_id)` unique), and a **create-card UI** that searches by provider type before falling back to manual **`no_provider`**.

## Assumptions
- Universal card API already supports catalog/manual modes (`catalog_item_id`, `provider` + `external_id`, `no_provider`).
- Existing RAWG transport exposes list/detail calls suitable for orchestration layers.
- Kinopoisk **keyword search** is authorized and rate-limited per product rules (≤ 5 req/s for search class endpoints).

## Step-by-Step Plan
1. **Schema**: Add **`game`** table and ORM **`Game`**; extend **`CatalogProvider`** with **`rawg`**; add nullable **`catalog_item.game_id`**; migration(s) + model tests for FK/uniqueness invariants surfaced in specs.
2. **RAWG services**: **`UpsertRawgGameService`** (list/detail merge semantics); **`SearchRawgGamesService`** (**local-first** DB search → **`search_games`** fallback → upsert **`Game`** rows + **`CatalogItem`**); snapshots JSONB/raw fields per blueprint.
3. **Kinopoisk transport + film search**: **`search-by-keyword`** in **`kinopoisk_provider_transport.py`**; **`SearchKinopoiskFilmsService`** mirroring **local-first** → remote merge; **`SearchLocalFilmsService`** extraction if not present.
4. **Coordinator**: **`SearchCatalogService`** routing `provider=` query param (`kinopoisk`|`rawg`); **`EnsureCatalogItemService`** / related ensure path stays single-writer idempotent boundary.
5. **API**: Implement **`GET /api/catalog/search?provider=&q=&page=`** returning normalized **`items[]`** (`kind`, `source`, `subtitle`, **`has_more`**); Pydantic schemas in **`api/catalog/schemas.py`**.
6. **Tests**: Extend **`backend/src/tests/api/test_catalog_routes.py`** (and service-level tests where patterns exist) covering local-only wins, RAWG persistence, Kinopoisk search branches, **`(provider, external_id)`** dedupe across local+provider, and downstream card creation expectations for RAWG-backed **`catalog_item_id`** where applicable.
7. **Frontend**: **`CreateCardPage`** multi-step flow: choose **film/series**, **game**, or **manual**; **typed search** wired to **`catalogApi`**; debounce + min chars; empty state links to manual; verification via **`npm run lint && npm run build`** plus manual smoke.
8. **Docs + logs**: Finish **`progress.md`** / **`result.md`**, update **`docs/features/catalog-search-providers.md`**, append action-log fragment after verification.

## Files Expected To Change
- `backend/src/models/catalog_item.py`, new `backend/src/models/game.py`, `backend/src/models/__init__.py`
- `backend/src/migrations/versions/*` (new revision(s))
- `backend/src/services/catalog/*` (**search**, **ensure**, RAWG upsert)
- `backend/src/providers/rawg/rawg_provider_transport.py` (only if wrappers missing)
- `backend/src/providers/kinopoisk/kinopoisk_provider_transport.py` (keyword search)
- `backend/src/api/catalog/routes.py`, `backend/src/api/catalog/schemas.py`
- `backend/src/tests/api/test_catalog_routes.py`, optional new test modules/helpers
- `frontend/src/pages/CreateCardPage.tsx`, `frontend/src/api/catalogApi.ts`, related UI components as needed

## Verification Plan
- **Backend:** `make backend-test` (Docker); targeted **`make backend-test-one target=…`** during development (`test_catalog_routes`, model tests).
- **Frontend:** `cd frontend && npm run lint && npm run build`.
- **Manual:** Film search (local vs remote), game search including first-hit upsert behavior, zero-result → manual, shelf/category unchanged from abstract-user-cards semantics.

## Risks And Mitigations
- Risk: **Provider quotas** exceeded during development or bursty UX.
  - Mitigation: min-length + debounce, backend query cache keyed by **`(provider, normalized_q, page)`**, throttle Kinopoisk search class separately.
- Risk: Duplicate rows when merging local + remote lists.
  - Mitigation: Deduplicate on **`(provider, external_id)`** in **`SearchCatalogService`** output ordering (local precedence where product agrees).
- Risk: **Game** migrations vs existing **`CatalogItem`** film-only assumptions in readers.
  - Mitigation: Gate new provider paths behind search + explicit **`kind`**; extend tests for non-film **`CatalogItem`** only where product reads require it.
