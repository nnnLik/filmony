# catalog-search-providers — progress

## 2026-05-14

### Schema / foundation (earlier)
- Added `Game` model (`backend/src/models/game.py`): RAWG-aligned columns, JSON snapshots, `search_synced_at` / `detail_synced_at`, unique `rawg_id`.
- Extended `CatalogProvider` with `rawg`; `CatalogItem.game_id` → `game.id` (nullable, CASCADE, indexed).
- Alembic revision **`p3q4r5s6t890`** (`p3q4r5s6t890_game_rawg_catalog.py`): `game` table + `catalog_item.game_id` FK.
- Tests: `backend/src/tests/models/test_game_catalog_schema.py`.

### RAWG local-first search + persistence (current)
- **Snapshot merge / DTO shaping:** `rawg_game_snapshot_utils.py` — list/detail merge without wiping unspecified fields (`merge_list_dto_into_game`, `merge_detail_dto_into_game`); naive UTC timestamps for TIMESTAMP WITHOUT TZ columns.
- **Upserts:** `UpsertRawgGameFromListDtoService`, `UpsertRawgGameFromDetailDtoService` (`build`, single `execute`).
- **Catalog item:** `EnsureRawgCatalogItemService` — `INSERT … ON CONFLICT` on `(provider, external_id)` updates `game_id`.
- **Search:** `SearchRawgCatalogGamesService` — ILIKE match on local `game`, then RAWG fallback; dedupe by `rawg_id`; normalizes hits via `RawgCatalogSearchHitDTO` (`provider`, `external_id`, `kind`, `title`, `subtitle`, `cover`, `source`, `catalog_item_id`). Calls `commit()` after `execute`.
- **`services.catalog` exports:** `__init__.py` re-exports new services.

### Tests
- `backend/src/tests/services/test_search_rawg_catalog_games_service.py`: local-only + ensured `CatalogItem`, remote list upsert + link, dedupe local vs remote overlap, ensure idempotent.
- Fragment log: `.cursor/memory/logs/2026-05-14T221500Z-catalog-search-providers-code.md`.

### Verification (Docker)
```bash
docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend ruff check --config pyproject.toml \
  src/services/catalog/rawg_catalog_search_hit_dto.py \
  src/services/catalog/rawg_game_snapshot_utils.py \
  src/services/catalog/upsert_rawg_game_from_list_dto_service.py \
  src/services/catalog/upsert_rawg_game_from_detail_dto_service.py \
  src/services/catalog/ensure_rawg_catalog_item_service.py \
  src/services/catalog/search_rawg_catalog_games_service.py \
  src/services/catalog/__init__.py \
  src/tests/services/test_search_rawg_catalog_games_service.py

docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend \
  pytest src/tests/services/test_search_rawg_catalog_games_service.py -v
```

### Notes / follow-ups (not blocking this slice)
- Wire `GET` (or RPC) catalog route wrapping `SearchRawgCatalogGamesService` when API contract for clients is finalized.
- `vars/.env.development`: align `RAWG_API_KEY` with `RAWG_SETTINGS` expectation (see `.env.example`).

### Catalog search API `GET /api/catalog/search` (2026-05-14)

- **`CatalogSearchProvider`**: `kinopoisk` \| `rawg` only (`no_provider` rejected by schema).
- **Query**: `q` trim then **≥ 3** chars (HTTP 422 if shorter); **`page`** ≥ 1, **`limit`** 1–40 default **15**.
- **`SearchRawgCatalogGamesService`**: returns `SearchRawgCatalogGamesResult` (`hits`, `has_more`); supports **`page` > 1** (remote-only slice); existing local-first semantics on page 1.
- **`GET /catalog/search`** (router prefix `/catalog`): authenticated; maps Kinopoisk `source=provider` → response `remote`; RAWG preserves `local`/`remote`; 502 on provider transport failures.
- **Tests**: extended `backend/src/tests/api/test_catalog_routes.py` — local-first + monkeypatched remote for RAWG and Kinopoisk, `no_provider`, short query.

### Kinopoisk local-first film search (2026-05-14)
- **DTOs:** `backend/src/providers/kinopoisk/kinopoisk_search_dto.py` — `KinopoiskFilmSearchItemDTO`, `KinopoiskFilmSearchResponseDTO`; transport maps API JSON; HTTP **404** → empty result object.
- **Transport:** `KinopoiskProviderTransport.search_films_by_keyword` → `GET /v2.1/films/search-by-keyword`.
- **Service:** `SearchKinopoiskFilmsLocalFirstService` (`search_kinopoisk_films_local_first.py`): page 1 queries local `Film` by `title ILIKE`, returns up to `PAGE_SIZE` (20) local hits first; skips outbound search when the first page is already full of local matches; otherwise merges provider hits, **upserts** `Film` + **`CatalogItem(provider=kinopoisk, external_id=str(kinopoisk_id), film_id)`**.
- **Tests:** `backend/src/tests/services/catalog/test_search_kinopoisk_films_local_first.py`. Run with resolve tests: `pytest src/tests/api/test_catalog_routes.py` **before** the services file if combining paths (ordering-sensitive with shared DB lifecycle in some sessions), or run files separately.
- **Verification:** `docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend pytest src/tests/api/test_catalog_routes.py src/tests/services/catalog/test_search_kinopoisk_films_local_first.py -v` — 7 passed. `uv run ruff check` on touched paths — pass.
- **Log fragment:** `.cursor/memory/logs/2026-05-14T222500Z-catalog-search-providers-code.md`.

### Frontend: create-card search-first (2026-05-15)

- **Шаг 1:** «Что добавляем?» — фильм/сериал (поиск Kinopoisk), игра (поиск RAWG), без каталога (ручной режим сохранён).
- **Клиент каталога:** `searchCatalog` + типы попадания в `frontend/src/api/catalogApi.ts`; debounce 450 ms; запросы только если нормализованный запрос ≥ 3 символов; `useInfiniteQuery` + «Показать ещё».
- **Привязка:** результат фильма → `catalog_film` (резолв `Film` по внешнему id KP для превью/дублей/«к просмотру»); игра → `catalog_game`, submit с `catalog_item_id` и `display_title` / `display_cover_url` / `display_summary`.
- **Kinopo по ссылке:** опционально, только для режима фильма (раскрываемый блок).
- **`UserCardProvider`:** добавлен `rawg`; см. также `frontend/src/lib/openExternalUrl.ts` для сигнатур KP-хелперов.
- **Проверка:** `cd frontend && npm run lint && npm run build` — успех.

## 2026-05-15 — Final verification (merge-ready check)

- **Backend (Docker):** `docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend pytest` — **247 passed** (~45s). Catalog-focused slice (catalog routes + catalog services + RAWG search service + game schema): **22 passed**.
- **Frontend:** `cd frontend && npm run lint && npm run build` — **pass**.
- **Ruff:** `make backend-lint` — **pass** after unused-local cleanup in `test_cards_routes.py` (see Lint cleanup below).

### Lint cleanup (2026-05-15)

- Removed unused `_login` result bindings in `test_cards_routes.py` (`me`, `owner`, `other`) — calls retained for setup side effects only.
- **Verification:** `make backend-lint` → **All checks passed**. `docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend pytest src/tests/api/test_cards_routes.py -q` → **53 passed** (~11s).
- **Env note:** `RawgSettings` requires `RAWG_API_KEY` at app import; use `RAWG_API_KEY` in `vars/.env.development` / `.env.example` (tests: pass `RAWG_API_KEY=test` on `docker compose exec` if the file omits it).
- **Plan steps 1–8:** Done; step 8 (docs/logs) closed with this update + `docs/features/catalog-search-providers.md` + action-log fragments.
