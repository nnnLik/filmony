# Action log fragment

- **Timestamp:** 2026-05-15T062000Z
- **Feature slug:** catalog-search-providers
- **Action type:** code
- **Summary:** RAWG transport now raises `RawgProviderTransportError` with safe, non-empty messages (HTTP status / JSON shape / generic upstream class); catalog `GET /search` logs `RAWG catalog search failed` with full traceback (`exc_info=True`) and structured `extra` without URLs or API keys. API 502 `detail` remains human-readable; fallback if message empty.
- **Files:** `backend/src/providers/rawg/rawg_provider_transport.py`, `backend/src/api/catalog/routes.py`, `backend/src/tests/api/test_catalog_routes.py`
- **Verification:**
  - `docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend ruff check --config pyproject.toml src/providers/rawg/rawg_provider_transport.py src/api/catalog/routes.py src/tests/api/test_catalog_routes.py` → **All checks passed**
  - `docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend pytest src/tests/api/test_catalog_routes.py -v` → **11 passed**
  - `docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend pytest src/tests/services/test_search_rawg_catalog_games_service.py -v` → **4 passed**
  - `make backend-lint` → **fails** on pre-existing `src/migrations/versions/bd8f039d04fe_card.py` (UP035/I001/UP007); not introduced by this change
- **Links:** `.cursor/active/catalog-search-providers/progress.md`
