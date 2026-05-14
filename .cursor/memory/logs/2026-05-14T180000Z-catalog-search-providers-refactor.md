# RAWG transport refactor

- Timestamp: 2026-05-14T180000Z
- Feature slug: `catalog-search-providers`
- Action type: `refactor`

## Summary

`RawgProviderTransportError` is a frozen dataclass with `msg` and `__str__` forwarding to `msg`. Removed `@staticmethod`; HTTP failure message normalization is `_safe_http_failure_message` (instance method). Shared `_fetch_json_then_parse_document` wraps HTTP and DTO-parse errors for `search_games` and `get_game` with unchanged user-facing strings.

## Files

- `backend/src/providers/rawg/rawg_provider_transport.py`

## Verification

```bash
make backend-lint
docker compose -f docker-compose.yml exec -e RAWG_API_KEY=test -w /opt/app backend pytest \
  src/tests/api/test_catalog_routes.py src/tests/services/test_search_rawg_catalog_games_service.py -q
```

Result: ruff pass; **15 passed**.
