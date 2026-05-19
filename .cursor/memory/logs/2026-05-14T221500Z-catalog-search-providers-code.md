## 2026-05-14T22:15:00Z

- Feature slug: `catalog-search-providers`
- Action type: `code`

### Summary
Implemented RAWG local-first catalog search orchestration (`SearchRawgCatalogGamesService`), PostgreSQL upsert-backed `EnsureRawgCatalogItemService`, list/detail game snapshot merge (`UpsertRawgGameFromListDtoService`, `UpsertRawgGameFromDetailDtoService`), snapshot helpers (`rawg_game_snapshot_utils`), normalized hit DTO (`RawgCatalogSearchHitDTO`), and pytest coverage under `backend/src/tests/services/test_search_rawg_catalog_games_service.py`.

### Files
- `backend/src/services/catalog/rawg_catalog_search_hit_dto.py`
- `backend/src/services/catalog/rawg_game_snapshot_utils.py`
- `backend/src/services/catalog/upsert_rawg_game_from_list_dto_service.py`
- `backend/src/services/catalog/upsert_rawg_game_from_detail_dto_service.py`
- `backend/src/services/catalog/ensure_rawg_catalog_item_service.py`
- `backend/src/services/catalog/search_rawg_catalog_games_service.py`
- `backend/src/services/catalog/__init__.py`
- `backend/src/tests/services/test_search_rawg_catalog_games_service.py`

### Verification
- `docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend ruff check …` → All checks passed
- `docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend pytest src/tests/services/test_search_rawg_catalog_games_service.py -v` → 4 passed
