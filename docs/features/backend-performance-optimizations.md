# Backend performance optimizations

## Summary

Improvements across HTTP provider calls, catalog search/resolve paths, reaction summaries, feed assembly, and card detail loading. External API behavior is unchanged.

## Provider HTTP

- Shared `httpx.AsyncClient` with connect/read/write/pool timeouts and connection limits.
- Retries on transport failures, HTTP 429 (honors `Retry-After` when present), and 5xx responses for idempotent GETs.

## Catalog

- **Redis-backed** JSON cache with single-flight loading for Kinopoisk film search, RAWG game search, and Kinopoisk resolve (cached as catalog + film ids, then reloaded in the request session).
- Keys are bounded as `filmony:catalog:v1:<segment>:<sha256(logical_key)[:32]>`.
- Optional observability: `services.catalog.redis_catalog_cache.catalog_cache_counters()` exposes `{hits, misses, errors}` (best-effort, non-transactional).
- Configuration (`backend/src/conf/settings.py`): `CATALOG_CACHE_REDIS_URL` (optional); TTL overrides `CATALOG_CACHE_SEARCH_TTL_SECONDS`, `CATALOG_CACHE_RESOLVE_TTL_SECONDS`. When `redis_url` is unset, **Redis `CELERY_BROKER_URL`** is used if it already uses the `redis://` / `rediss://` scheme (prefer a **separate Redis logical DB** in production to isolate Celery broker traffic).
- Caching is **disabled when `ENV=test`** to keep tests deterministic (no Redis dependency for pytest).

## Reactions

- Embedded reactors for summary payloads are limited in the database using a window function (up to 25 per target and reaction type), avoiding unbounded actor rows.
- Grouped reaction counts and the viewer’s reaction-type (“mine”) list share **one aggregate query** via PostgreSQL `bool_or(user_reaction.user_id = :viewer)` per `(target_kind, target_id, reaction_type_id)` group — removing a second round-trip that scanned the same scope.
- Alembic adds `ix_user_reaction_target_kind_type_id` on `(target_kind, target_id, reaction_type_id, id DESC)` to match the hot reactor window path.
- Follow-up migration **`z9y8x7w65431`** drops legacy `ix_user_reaction_target` because the composite index supplies the same `(target_kind, target_id)` prefix. Capture `pg_stat_user_indexes` after warmup to validate zero/low reliance before rollout if your dataset diverges.

## Feed

- Global feed: removed a redundant second pass that re-enriched feed posts already enriched when hydrating posts.
- Personal merged feed: card hydration and post hydration run concurrently with `asyncio.gather` where independent.

## Card details

- Loads `UserCard`, author `User`, and `Film` in one statement, resolving film via `coalesce(movie_card.film_id, catalog_item.film_id)` when needed.
- Tags, category row, and reaction summaries load concurrently via `asyncio.gather`.

## Database sessions in Celery

- `disposable_async_session` continues to use a **fresh async engine per invocation** so Telegram notification tasks (which run under `asyncio.run` in a Celery worker thread) do not reuse the FastAPI process pool tied to a different event loop. Reducing engine churn further requires a **pool keyed by running loop** (documented follow-up).

## Migrations

- Apply: `alembic upgrade head` — includes `r0s1t2u3v456` (reactor window index) then **`z9y8x7w65431`** (drop redundant `ix_user_reaction_target`).

## Evidence checklist (indexes)

Run against staging/production after traffic warmup:

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

Expect use of `ix_user_reaction_target_kind_type_id` rather than the removed duplicate btree.
