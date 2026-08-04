# Action log fragment

- **Timestamp:** 2026-05-15T030000Z
- **Feature slug:** catalog-search-providers
- **Action type:** test
- **Summary:** Full backend pytest in Docker with `RAWG_API_KEY=test`; catalog-focused subset; cleared `backend/src/**/__pycache__`. `make backend-lint` failed (3× F841 in `test_cards_routes.py`).
- **Files:** `backend/src/tests/api/test_catalog_routes.py`, `backend/src/tests/services/catalog/`, `backend/src/tests/services/test_search_rawg_catalog_games_service.py`, `backend/src/tests/models/test_game_catalog_schema.py` (scope of catalog tests); `.cursor/active/catalog-search-providers/result.md`
- **Verification:**
  - `docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend pytest` → **247 passed** (~45s)
  - `docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend pytest src/tests/api/test_catalog_routes.py src/tests/services/catalog/ src/tests/services/test_search_rawg_catalog_games_service.py src/tests/models/test_game_catalog_schema.py` → **22 passed**
  - `cd frontend && npm run lint && npm run build` → **pass**
  - `make backend-lint` → **fail** (`F841` in `backend/src/tests/api/test_cards_routes.py` ~1701, 1755, 1756)
- **Links:** `docs/features/catalog-search-providers.md`, `.cursor/active/catalog-search-providers/progress.md`
