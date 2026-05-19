# Action: catalog-search-providers (code)

- **Timestamp:** 2026-05-14T210000Z
- **Feature slug:** catalog-search-providers
- **Action type:** code
- **Summary:** Game table/model foundation for RAWG catalog: `Game` ORM, `CatalogProvider.rawg`, nullable `CatalogItem.game_id` FK, Alembic migration `p3q4r5s6t890`, focused schema tests.
- **Files:**
  - `backend/src/models/game.py`
  - `backend/src/models/catalog_item.py`
  - `backend/src/models/__init__.py`
  - `backend/src/migrations/versions/p3q4r5s6t890_game_rawg_catalog.py`
  - `backend/src/tests/models/test_game_catalog_schema.py`
  - `.cursor/active/catalog-search-providers/progress.md`
  - `.cursor/memory/logs/action-log.md`
- **Verification:**
  - `docker compose -f docker-compose.yml run --rm backend ruff check` (paths above) — pass
  - `docker compose -f docker-compose.yml run --rm -e RAWG_API_KEY=test backend pytest src/tests/models/test_game_catalog_schema.py -q` — 4 passed
