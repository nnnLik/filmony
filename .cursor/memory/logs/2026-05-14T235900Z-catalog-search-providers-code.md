# catalog-search-providers — code

- **Timestamp**: 2026-05-14T235900Z
- **Feature slug**: catalog-search-providers
- **Action type**: code

## Summary

Added `GET /api/catalog/search` with provider-agnostic payload (`provider`, `external_id`, `kind`, `title`, `subtitle`, `cover_url`, `catalog_item_id`, `source`), `has_more`, and query validation (`q` trimmed ≥ 3 chars, `limit`/`page`). Extended RAWG catalog search service to return `SearchRawgCatalogGamesResult` and honor `page` for remote paging.

## Files

- `backend/src/api/catalog/schemas.py`
- `backend/src/api/catalog/routes.py`
- `backend/src/services/catalog/search_rawg_catalog_games_service.py`
- `backend/src/services/catalog/__init__.py`
- `backend/src/tests/api/test_catalog_routes.py`
- `backend/src/tests/services/test_search_rawg_catalog_games_service.py`

## Verification

```bash
docker compose -f docker-compose.yml exec -w /opt/app backend \
  /opt/pysetup/.venv/bin/ruff check --config pyproject.toml \
    src/api/catalog/routes.py \
    src/api/catalog/schemas.py \
    src/services/catalog/search_rawg_catalog_games_service.py \
    src/services/catalog/__init__.py \
    src/tests/api/test_catalog_routes.py \
    src/tests/services/test_search_rawg_catalog_games_service.py

docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend \
  /opt/pysetup/.venv/bin/pytest \
    src/tests/api/test_catalog_routes.py \
    src/tests/services/test_search_rawg_catalog_games_service.py -v --tb=short
```

Outcome: **ruff**: all checks passed; **pytest**: 14 passed.
