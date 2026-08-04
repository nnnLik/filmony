# Action log fragment

- **Timestamp:** 2026-05-14T235500Z
- **Feature slug:** catalog-search-providers
- **Action type:** code

## Summary

Normalized catalog search `q` everywhere: trim, collapse internal whitespace, lowercase. Frontend debounce and React Query key use normalized text so case-only and whitespace-only edits do not refetch. Backend route and search services normalize defensively before validation, cache keys, and provider calls.

## Files

- `backend/src/services/catalog/catalog_search_query_normalize.py` (new)
- `backend/src/api/catalog/routes.py`
- `backend/src/services/catalog/search_kinopoisk_films_local_first.py`
- `backend/src/services/catalog/search_rawg_catalog_games_service.py`
- `backend/src/tests/api/test_catalog_routes.py`
- `backend/src/tests/services/test_search_rawg_catalog_games_service.py`
- `backend/src/tests/services/catalog/test_catalog_search_query_normalize.py` (new)
- `frontend/src/lib/normalizeCatalogSearchQuery.ts` (new)
- `frontend/src/api/catalogApi.ts`
- `frontend/src/pages/CreateCardPage.tsx`

## Verification

- `docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend pytest src/tests/api/test_catalog_routes.py src/tests/services/test_search_rawg_catalog_games_service.py src/tests/services/catalog/test_catalog_search_query_normalize.py src/tests/services/catalog/test_search_kinopoisk_films_local_first.py -q` → **22 passed**
- `docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend ruff check --config pyproject.toml` (touched backend paths) → **All checks passed**
- `cd frontend && npm run lint && npm run build` → **pass**
