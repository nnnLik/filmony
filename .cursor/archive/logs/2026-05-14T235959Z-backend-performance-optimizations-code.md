# 2026-05-14T235959Z — backend-performance-optimizations — code

- **Timestamp:** 2026-05-14T23:59:59Z  
- **Feature slug:** backend-performance-optimizations  
- **Action type:** code  

## Summary

Implemented shared HTTP client with retries, catalog TTL coalescing caches, SQL-windowed reaction reactors + index migration, global feed enrichment dedupe, parallel feed hydration, consolidated card-details query, and unit test for the cache helper.

## Files

- `backend/src/providers/shared_async_http.py`
- `backend/src/providers/base_provider_http_transport.py`
- `backend/src/services/kinopoisk/client.py`
- `backend/src/core/database.py`
- `backend/src/services/catalog/ttl_coalescing_cache.py`
- `backend/src/services/catalog/search_kinopoisk_films_local_first.py`
- `backend/src/services/catalog/search_rawg_catalog_games_service.py`
- `backend/src/services/catalog/resolve_catalog_item_service.py`
- `backend/src/services/reactions/get_reaction_summaries_for_targets.py`
- `backend/src/services/feed/list_global_feed.py`
- `backend/src/services/cards/list_movie_card_feed.py`
- `backend/src/services/cards/get_movie_card_details.py`
- `backend/src/models/user_reaction.py`
- `backend/src/migrations/versions/r0s1t2u3v456_user_reaction_reactor_window_index.py`
- `backend/src/tests/services/catalog/test_ttl_coalescing_cache.py`
- `docs/features/backend-performance-optimizations.md`
- `.cursor/features/backend-performance-optimizations/feature.md`
- `.cursor/active/backend-performance-optimizations/plan.md`
- `.cursor/active/backend-performance-optimizations/progress.md`
- `.cursor/active/backend-performance-optimizations/result.md`

## Verification

- `docker compose exec … ruff check` on edited modules: passed.
- `docker compose exec … pytest` (targeted paths + API batches) with `RAWG_API_KEY` / `KINOPOISK_API_KEY`: passed in runs documented in `result.md`. Full-tree suite may deadlock on shared Postgres under parallel load — use exclusive DB for CI.
