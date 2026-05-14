# Progress: backend-performance-optimizations

- Implemented provider shared HTTP + retries; Kinopoisk client uses the same helper.
- Implemented TTL coalescing cache (skipped when `ENV=test`).
- Reactions: windowed actor query; new index migration.
- Global feed: dropped second inline-ref enrichment pass.
- Personal feed: parallel card/post hydration branches.
- Get card details: single `UserCard`/`User`/`Film` select.
- `disposable_async_session`: kept per-call dedicated engine (Celery `asyncio.run` in thread pool); documented pool-per-loop as follow-up.
- Tests: `test_ttl_coalescing_cache.py`; catalog/global feed/cards previously run green.
