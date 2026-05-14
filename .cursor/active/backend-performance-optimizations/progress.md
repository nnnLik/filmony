# Progress: backend-performance-optimizations

- Implemented provider shared HTTP + retries; Kinopoisk client uses the same helper.
- Catalog: Redis-backed JSON cache + single-flight coalescing (`redis_catalog_cache.py`); bounded keys (`filmony:catalog:v1:<segment>:sha256[:32]`); module counters (`catalog_cache_counters`). Skipped when `ENV=test`. URL: `CATALOG_CACHE_REDIS_URL` or Redis `CELERY_BROKER_URL` fallback.
- Legacy in-process TTL helper retained only for unit tests (`ttl_coalescing_cache.TtlCoalescingCache`).
- Reactions: windowed actor query; composite index migration (`r0s1…`); count + viewer mine merged via `bool_or` in grouped aggregate (one fewer DB round-trip).
- Drop redundant `ix_user_reaction_target` (`z9y8x7w65431`) — superseded by `ix_user_reaction_target_kind_type_id` prefix; ORM model aligned.
- Merge migration `m3n4o5p89012`: joins heads `k7l8m9n0o123` + `z9y8x7w65431` (no-op upgrade/downgrade) so Alembic has a single linear head again.
- Global feed: dropped second inline-ref enrichment pass.
- Personal feed: parallel card/post hydration branches.
- Get card details: single `UserCard`/`User`/`Film` select; tags / category / reaction summaries fetched with `asyncio.gather`.
- `disposable_async_session`: kept per-call dedicated engine (Celery `asyncio.run` in thread pool); documented pool-per-loop as follow-up.
- Tests: targeted catalog + reactions routes + RAWG search + TTL cache (`docker compose run … pytest`, 23 passed).
