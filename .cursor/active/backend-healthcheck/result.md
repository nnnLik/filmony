# backend-healthcheck — result

**Status:** completed

## Implemented

- `GET /health` — liveness probe; public, no auth; returns `200` with `{"status":"ok"}` without touching dependencies.
- `GET /health/ready` — readiness probe; public, no auth; checks Postgres (`SELECT 1`) and Redis (`PING`); returns `200` when all checks pass, `503` when any fails; JSON includes per-check status for `postgres` and `redis`.
- `CheckBackendReadinessService` orchestrates dependency checks with typed result DTOs.
- Health routes registered on the FastAPI app via `app_utils.py`.
- Docker Compose `healthcheck` on the `backend` service in `docker-compose.yml` and `docker-compose.prod.yml` (probes `/health/ready`).

## Changed files

- `backend/src/api/health/routes.py`
- `backend/src/api/health/schemas.py`
- `backend/src/services/health/check_backend_readiness.py`
- `backend/src/utils/app_utils.py`
- `backend/src/tests/integration/api/test_health_routes.py`
- `backend/src/tests/unit/services/health/test_check_backend_readiness.py`
- `docker-compose.yml`
- `docker-compose.prod.yml`

## Verification

```bash
make backend-test-one target=src/tests/integration/api/test_health_routes.py
make backend-test-one target=src/tests/unit/services/health/test_check_backend_readiness.py
```

Both passed (integration: liveness + readiness happy path; unit: Redis URL resolution + postgres failure still evaluates redis).

## Known limitations

- Does not verify the Celery worker process itself — only that Redis (broker) responds to `PING`.
- Does not probe external APIs (Kinopoisk, Telegram, TMDB, etc.).
- Does not check RustFS / object storage connectivity.
- Redis URL resolution prefers `CELERY_BROKER_URL` when it starts with `redis://` or `rediss://`; falls back to `CATALOG_CACHE_REDIS_URL`, then `WATCH_PARTY_REDIS_URL`.
