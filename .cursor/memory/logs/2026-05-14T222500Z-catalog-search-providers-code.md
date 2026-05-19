# Action: catalog-search-providers (code)

- **Timestamp:** 2026-05-14T222500Z
- **Feature slug:** catalog-search-providers
- **Action type:** code
- **Summary:** Kinopoisk keyword search transport (`/v2.1/films/search-by-keyword`), search DTOs, `SearchKinopoiskFilmsLocalFirstService` (local `Film` ILIKE then provider merge, persist `Film` + `CatalogItem`), tests with fake transport.
- **Files:**
  - `backend/src/providers/kinopoisk/kinopoisk_search_dto.py`
  - `backend/src/providers/kinopoisk/kinopoisk_provider_transport.py`
  - `backend/src/providers/kinopoisk/__init__.py`
  - `backend/src/services/catalog/search_kinopoisk_films_local_first.py`
  - `backend/src/services/catalog/__init__.py`
  - `backend/src/tests/services/catalog/test_search_kinopoisk_films_local_first.py`
  - `.cursor/active/catalog-search-providers/progress.md`
  - `.cursor/memory/logs/action-log.md`
- **Verification:**
  - `uv run ruff check` (touched backend paths) — pass
  - `docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend pytest src/tests/api/test_catalog_routes.py src/tests/services/catalog/test_search_kinopoisk_films_local_first.py -v` — 7 passed
