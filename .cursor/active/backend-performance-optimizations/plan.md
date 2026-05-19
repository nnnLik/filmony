# Plan: backend-performance-optimizations

1. Provider transport: shared `httpx.AsyncClient`, granular timeouts, retry/backoff on idempotent GET (429/5xx).
2. DB `disposable_async_session`: avoid cross-loop use of the FastAPI engine; document pool-per-loop follow-up for Celery threads.
3. Catalog: Redis JSON cache + in-flight coalescing for kinopoisk/rawg search and resolve id pairs (bounded keys; non-test only); counters for observability.
4. Reactions: limit embedded reactors in SQL (`row_number` per target × reaction type); merge viewer mine aggregation into grouped count query (`bool_or`).
5. Feed: remove redundant global-feed post enrichment; `asyncio.gather` card vs post hydration in merged feed.
6. Card details: single query with `coalesce(film_id, catalog_item→film_id)`; parallelize tags/category/reactions tail queries (`asyncio.gather`).
7. Migration: composite index matching reactor window query; drop redundant `(target_kind, target_id)` btree superseded by composite prefix index.
