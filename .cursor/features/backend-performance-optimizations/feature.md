# Feature: backend-performance-optimizations

## Scope

Reduce hotspots: provider HTTP (shared client, timeouts, retries), catalog search caching/coalescing, reaction summary actor fetch, feed hydration, card detail queries, and index coverage for hot SQL.

## Acceptance criteria

- No intentional API contract changes.
- Backend tests for touched behavior pass (Docker `pytest` where the DB is available).
- Alembic migration for justified new indexes.
