# Backend performance optimizations

## Summary

Improvements across HTTP provider calls, catalog search/resolve paths, reaction summaries, feed assembly, and card detail loading. External API behavior is unchanged.

## Provider HTTP

- Shared `httpx.AsyncClient` with connect/read/write/pool timeouts and connection limits.
- Retries on transport failures, HTTP 429 (honors `Retry-After` when present), and 5xx responses for idempotent GETs.

## Catalog

- In-process TTL cache with request coalescing for Kinopoisk film search, RAWG game search, and Kinopoisk resolve (cached as catalog + film ids, then reloaded in the request session).
- Caching is **disabled when `ENV=test`** to keep tests deterministic.

## Reactions

- Embedded reactors for summary payloads are limited in the database using a window function (up to 25 per target and reaction type), avoiding unbounded actor rows.
- Alembic adds `ix_user_reaction_target_kind_type_id` on `(target_kind, target_id, reaction_type_id, id DESC)` to match the hot path.

## Feed

- Global feed: removed a redundant second pass that re-enriched feed posts already enriched when hydrating posts.
- Personal merged feed: card hydration and post hydration run concurrently with `asyncio.gather` where independent.

## Card details

- Loads `UserCard`, author `User`, and `Film` in one statement, resolving film via `coalesce(movie_card.film_id, catalog_item.film_id)` when needed.

## Database sessions in Celery

- `disposable_async_session` continues to use a **fresh async engine per invocation** so Telegram notification tasks (which run under `asyncio.run` in a Celery worker thread) do not reuse the FastAPI process pool tied to a different event loop. Reducing engine churn further requires a **pool keyed by running loop** (documented follow-up).

## Migration

- Apply: `alembic upgrade head` (revision `r0s1t2u3v456`).
