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

## 2026-05-15 — RAWG catalog 502 observability

- **Transport:** `RawgProviderTransportError` exposes **`msg`** (dataclass Exception); HTTP failures map to safe strings (`unexpected status N`, invalid JSON/root, or `upstream request failed (ProviderHttpError)` without echoing raw httpx text that might contain URLs). Parse failures include `failed to parse RAWG games search response` / game detail variant.
- **Route:** `GET /catalog/search` (rawg branch) logs `logger.error(..., exc_info=True, extra={catalog_provider, error_message})` before HTTP 502.
- **Tests:** `test_catalog_search_rawg_transport_failure_502_non_empty_detail` — asserts non-empty `detail` and log excerpt includes transport + cause types.
- **Verification:** `ruff check` on touched paths; `pytest src/tests/api/test_catalog_routes.py` and `pytest src/tests/services/test_search_rawg_catalog_games_service.py` with `RAWG_API_KEY=test`.
- **Log fragment:** `.cursor/memory/logs/2026-05-15T062000Z-catalog-search-providers-code.md`

### RAWG transport refactor (2026-05-14)

- **`RawgProviderTransportError`:** `@dataclass(slots=True, frozen=True)` with `msg`; `str(e)` non-empty via `__str__`.
- **No `staticmethod`:** `_safe_http_failure_message` is an instance method; shared `_fetch_json_then_parse_document` handles HTTP and DTO-parse errors for search + detail (same user-visible strings as before; no API key in messages).
- **Verification:** `make backend-lint`; `pytest src/tests/api/test_catalog_routes.py src/tests/services/test_search_rawg_catalog_games_service.py` with `RAWG_API_KEY=test` — 15 passed.
- **Log fragment:** `.cursor/memory/logs/2026-05-14T180000Z-catalog-search-providers-refactor.md`.

## 2026-05-15 — Final verification (merge-ready check)

- **Backend (Docker):** `docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend pytest` — **247 passed** (~45s). Catalog-focused slice (catalog routes + catalog services + RAWG search service + game schema): **22 passed**.
- **Frontend:** `cd frontend && npm run lint && npm run build` — **pass**.
- **Ruff:** `make backend-lint` — **pass** after migration `bd8f039d04fe_card.py` style fixes (see Migration lint-only) and unused-local cleanup in `test_cards_routes.py` (Lint cleanup below).

### Migration lint-only (2026-05-15)

- **`bd8f039d04fe_card.py`:** Ruff-only fixes (`collections.abc.Sequence`, PEP 604 union types on revision metadata, sorted imports); removed stray unused `typing.Union` after auto-fix — **no SQL / Alembic behavior change**.
- **Verification:** `make backend-lint` → **All checks passed**.
- **Log fragment:** `.cursor/memory/logs/2026-05-15T071500Z-catalog-search-providers-test.md`.

### Lint cleanup (2026-05-15)

- Removed unused `_login` result bindings in `test_cards_routes.py` (`me`, `owner`, `other`) — calls retained for setup side effects only.
- **Verification:** `make backend-lint` → **All checks passed**. `docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend pytest src/tests/api/test_cards_routes.py -q` → **53 passed** (~11s).
- **Env note:** `RawgSettings` requires `RAWG_API_KEY` at app import; use `RAWG_API_KEY` in `vars/.env.development` / `.env.example` (tests: pass `RAWG_API_KEY=test` on `docker compose exec` if the file omits it).
- **Plan steps 1–8:** Done; step 8 (docs/logs) closed with this update + `docs/features/catalog-search-providers.md` + action-log fragments.
