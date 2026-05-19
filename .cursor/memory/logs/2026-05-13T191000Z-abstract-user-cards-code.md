# Action log

- **Timestamp:** 2026-05-13T191000Z
- **Feature slug:** abstract-user-cards
- **Action type:** code

## Summary

Added provider-oriented catalog resolve API: `POST /api/catalog/resolve` (Kinopoisk URL) via `ResolveCatalogItemService`, ensuring `CatalogItem(provider='kinopoisk', external_id=…)` is linked to the resolved `Film`. Response includes catalog identity, display fields, and nested `FilmResponse` for compatibility.

## Files

- `backend/src/api/catalog/routes.py`
- `backend/src/api/catalog/schemas.py`
- `backend/src/api/router.py`
- `backend/src/services/catalog/resolve_catalog_item_service.py`
- `backend/src/services/catalog/__init__.py`
- `backend/src/tests/api/test_catalog_routes.py`

## Verification

- `make backend-test-one target=src/tests/api/test_catalog_routes.py` — 3 passed
- `make backend-test-one target='src/tests/api/test_cards_routes.py -k resolve_film'` — 3 passed
- `docker compose exec -w /opt/app backend ruff check src/api/catalog src/services/catalog src/api/router.py` — clean
