# Result: backend-performance-optimizations

## Implemented

| Area | Change | Rationale |
|------|--------|-----------|
| HTTP providers | `providers/shared_async_http.py`: process-wide `httpx.AsyncClient`, granular timeouts, retry on 429/5xx + `Retry-After` | Fewer TCP/TLS handshakes; resilient to rate limits and transient upstream errors |
| Base transport | `BaseProviderHttpTransport.get` uses shared client | Same as above |
| Kinopoisk client | `services/kinopoisk/client.py` uses shared GET w/ retry | Aligns with provider stack |
| DB disposable session | `disposable_async_session` uses short-lived engine per call (restored) | Celery tasks run `asyncio.run` in a **worker thread** (different event loop than FastAPI). Sharing the app engine caused asyncpg “wrong loop” errors. **Follow-up:** keyed pool per `id(asyncio.get_running_loop())` to reduce churn without cross-loop sharing. |
| Catalog cache | `services/catalog/ttl_coalescing_cache.py` + wire search/resolve | TTL (~45s search / ~60s resolve ids) + single flight per key; **disabled in tests** |
| Reactions | `row_number` subquery caps reactors at 25 in SQL | Avoids scanning unlimited rows per target |
| Index | `ix_user_reaction_target_kind_type_id` (…, `id DESC`) | Supports window predicate |
| Global feed | Removed duplicate `enrich_feed_post_items_for_feed_paths` | Posts already enriched in `attach_feed_post_list_engagement` |
| Merged feed | `asyncio.gather` for card vs post hydration | Independent I/O overlap |
| Card details | One `outerjoin` Film on `coalesce(user_card.film_id, catalog_item.film_id)` | Fewer round-trips |

## Verification

- `docker compose exec … pytest` with `RAWG_API_KEY` / `KINOPOISK_API_KEY` set: targeted modules passed (catalog, global feed, cards, feed_posts batches earlier at 80+).
- Full suite can hit **Postgres deadlocks** on `drop_all` when another client holds locks (environment); use an exclusive test DB when running the full tree.
- `ruff check` on touched modules: clean.

## Fixed vs partial vs deferred

| Original ask | Status | Note |
|--------------|--------|------|
| Provider shared client + timeouts + retry GET | **Fixed** | `shared_async_http.py` |
| DB disposable without engine churn | **Partial / deferred** | Per-call engine kept for Celery/thread loop safety; pool-per-loop documented |
| Catalog TTL + coalescing | **Fixed** | Non-test only |
| Reactions SQL cap | **Fixed** | + index |
| Global feed duplicate enrichment | **Fixed** | |
| Feed `gather` | **Fixed** | |
| Card details query shape | **Fixed** | |
| Index hygiene | **Partial** | Added one justified index; no broad drop of legacy indexes |

## Files touched (main)

- `backend/src/providers/shared_async_http.py` (new)
- `backend/src/providers/base_provider_http_transport.py`
- `backend/src/services/kinopoisk/client.py`
- `backend/src/core/database.py`
- `backend/src/services/catalog/ttl_coalescing_cache.py` (new)
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
