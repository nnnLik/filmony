# Action log fragment

- **Timestamp:** 2026-05-14T230000Z  
- **Feature slug:** catalog-search-providers  
- **Action type:** code  

## Summary

RAWG `Game` / `GameSingle` DTO fields that OpenAPI documents as `object` but the live API returns as JSON arrays (`ratings`, `added_by_status`, `reactions`) now parse as immutable `Mapping` or shallow `tuple` (list) without `RawgGameDtoParseError`. Added `rawg_open_blob_to_plain_json` for snapshots and `game.*_json` columns. Regression tests cover empty and populated `ratings` lists plus `added_by_status` as list.

## Files

- `backend/src/providers/rawg/rawg_openapi_dto.py` — `_open_object_or_array`, `RawgOpenObjectOrArray`, `rawg_open_blob_to_plain_json`; DTO field types and `from_dict` wiring.  
- `backend/src/services/catalog/rawg_game_snapshot_utils.py` — persist list or dict blobs via `rawg_open_blob_to_plain_json`.  
- `backend/src/tests/providers/test_rawg_openapi_dto_ratings_blob.py` — list `ratings` / `added_by_status` parsing tests.  

## Verification

```bash
docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend ruff check --config pyproject.toml \
  src/providers/rawg/rawg_openapi_dto.py \
  src/services/catalog/rawg_game_snapshot_utils.py \
  src/tests/providers/test_rawg_openapi_dto_ratings_blob.py

docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend pytest \
  src/tests/providers/test_rawg_openapi_dto_ratings_blob.py \
  src/tests/services/test_search_rawg_catalog_games_service.py \
  src/tests/api/test_catalog_routes.py -q
```

Result: ruff **pass**; pytest **20 passed**.
