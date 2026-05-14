# Result: backend-performance-optimizations

## Implemented

| Area | Change | Rationale |
|------|--------|-----------|
| HTTP providers | `providers/shared_async_http.py`: process-wide `httpx.AsyncClient`, granular timeouts, retry on 429/5xx + `Retry-After` | Fewer TCP/TLS handshakes; resilient to rate limits and transient upstream errors |
| Base transport | `BaseProviderHttpTransport.get` uses shared client | Same as above |
| Kinopoisk client | `services/kinopoisk/client.py` uses shared GET w/ retry | Aligns with provider stack |
| DB disposable session | `disposable_async_session` uses short-lived engine per call (restored) | Celery tasks run `asyncio.run` in a **worker thread** (different event loop than FastAPI). Sharing the app engine caused asyncpg “wrong loop” errors. **Follow-up:** keyed pool per `id(asyncio.get_running_loop())` to reduce churn without cross-loop sharing. |
| Catalog cache | `redis_catalog_cache.py` + serializers colocated with Kinopoisk/RAWG services + resolve ids | Cross-process TTL via Redis; SHA256-truncated logical keys; in-flight coalescing; counters for observability; **skipped when `ENV=test`** |
| Catalog settings | `CatalogCacheSettings`: `CATALOG_CACHE_REDIS_URL`, TTL env overrides | Dedicated Redis DB recommended vs Celery broker |
| Reactions | `row_number` subquery caps reactors at 25 in SQL | Avoids scanning unlimited rows per target |
| Reactions aggregate | `bool_or(user_id == viewer)` inside grouped count query | Removes separate “mine” SELECT |
| Index | `ix_user_reaction_target_kind_type_id` (…, `id DESC`) | Supports window predicate |
| Index hygiene | Drop `ix_user_reaction_target` (`z9y8x7w65431`); remove from SQLAlchemy model | Redundant prefix vs composite window index (see evidence below) |
| Global feed | Removed duplicate `enrich_feed_post_items_for_feed_paths` | Posts already enriched in `attach_feed_post_list_engagement` |
| Merged feed | `asyncio.gather` for card vs post hydration | Independent I/O overlap |
| Card details | One `outerjoin` Film on `coalesce(user_card.film_id, catalog_item.film_id)` | Fewer SQL round-trips |
| Card details tail | `asyncio.gather` tags + category + reaction summaries | Parallel tail latency |

## Index evidence summary

Live `pg_stat_user_indexes` / `EXPLAIN` were **not captured** here because the development Postgres (`homelab-postgres`) was unreachable from this workspace session (`docker compose exec backend` service was stopped). Decisions rely on query-shape analysis and btree prefix rules:

| Index | Decision | Evidence basis |
|-------|----------|----------------|
| `ix_user_reaction_target` `(target_kind, target_id)` | **Dropped** | Hot summaries scan/filter by `(target_kind, target_id)`; `ix_user_reaction_target_kind_type_id` shares the same leading columns and additionally matches reactor ordering (`id DESC`). Narrow duplicate btree removed to save write amplification and planner ambiguity. |
| `ix_user_reaction_target_kind_type_id` | **Keep** | Window / grouped aggregates over partitions keyed by `(target_kind, target_id, reaction_type_id)` ordered by `id DESC`. |
| `ix_user_reaction_user_target_kind` | **Keep** | Viewer-target scoped lookups (`user_id`, `target_kind`, `target_id`). |
| `ix_user_reaction_reaction_type_id` | **Keep** | FK maintenance / rare global scans by type; cheap insurance vs cascading deletes on `reaction_type`. |

**Post-deploy checklist** (run against prod/staging after warmup):

```sql
SELECT indexrelname, idx_scan, idx_tup_read, pg_relation_size(indexrelid) AS bytes
FROM pg_stat_user_indexes
WHERE schemaname = 'public' AND relname = 'user_reaction'
ORDER BY indexrelname;

EXPLAIN (ANALYZE, BUFFERS)
SELECT target_kind, target_id, reaction_type_id, COUNT(*)
FROM user_reaction
WHERE target_kind = 'CARD' AND target_id = 1
GROUP BY target_kind, target_id, reaction_type_id;
```

Expect index use on `ix_user_reaction_target_kind_type_id` (or bitmap OR across targets), not the dropped duplicate.

## Verification

- `docker compose run --rm --no-deps backend pytest src/tests/services/catalog/test_ttl_coalescing_cache.py src/tests/services/test_search_rawg_catalog_games_service.py src/tests/api/test_reactions_routes.py src/tests/api/test_catalog_routes.py -q` → **23 passed**
- `uv run ruff check src/services/catalog/redis_catalog_cache.py` → clean

Apply migrations: `alembic upgrade head` — chain ends with `z9y8x7w65431` after `r0s1t2u3v456`.

## Fixed vs partial vs deferred

| Original ask | Status | Note |
|--------------|--------|------|
| Provider shared client + timeouts + retry GET | **Fixed** | `shared_async_http.py` |
| DB disposable without engine churn | **Partial / deferred** | Per-call engine kept for Celery/thread loop safety; pool-per-loop documented |
| Catalog Redis cache | **Fixed** | Non-test only; bounded keys + counters |
| Reactions SQL cap | **Fixed** | + merged mine aggregate |
| Global feed duplicate enrichment | **Fixed** | |
| Feed `gather` | **Fixed** | |
| Card details query shape | **Fixed** | |
| Card details tail batching | **Fixed** | `asyncio.gather` |
| Index hygiene | **Partial / evidence pending live stats** | One redundant btree dropped with documented rationale; run pg_stat checklist above |

## Files touched (this increment)

- `backend/src/conf/settings.py`
- `backend/src/services/catalog/redis_catalog_cache.py` (new)
- `backend/src/services/catalog/search_kinopoisk_films_local_first.py`
- `backend/src/services/catalog/search_rawg_catalog_games_service.py`
- `backend/src/services/catalog/resolve_catalog_item_service.py`
- `backend/src/services/catalog/ttl_coalescing_cache.py`
- `backend/src/services/cards/get_movie_card_details.py`
- `backend/src/services/reactions/get_reaction_summaries_for_targets.py`
- `backend/src/models/user_reaction.py`
- `backend/src/migrations/versions/z9y8x7w65431_drop_ix_user_reaction_target.py` (new)
- `backend/pyproject.toml`, `backend/uv.lock`
- `docs/features/backend-performance-optimizations.md`
