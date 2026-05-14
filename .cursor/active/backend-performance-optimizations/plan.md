# Plan: backend-performance-optimizations

1. Provider transport: shared `httpx.AsyncClient`, granular timeouts, retry/backoff on idempotent GET (429/5xx).
2. DB `disposable_async_session`: avoid cross-loop use of the FastAPI engine; document pool-per-loop follow-up for Celery threads.
3. Catalog: TTL + in-flight coalescing cache for kinopoisk/rawg search and resolve id cache (non-test only).
4. Reactions: limit embedded reactors in SQL (`row_number` per target × reaction type).
5. Feed: remove redundant global-feed post enrichment; `asyncio.gather` card vs post hydration in merged feed.
6. Card details: single query with `coalesce(film_id, catalog_item→film_id)`.
7. Migration: composite index matching reactor window query.
