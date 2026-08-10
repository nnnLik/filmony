# Backend health probes

HTTP liveness and readiness endpoints for the Filmony backend. Used by Docker Compose healthchecks, load balancers, and deploy pipelines to decide whether a backend instance is alive and can accept traffic.

## Endpoints

Both routes are **public** (no auth).

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/health` | **Liveness** — process is up; no dependency checks |
| GET | `/health/ready` | **Readiness** — Postgres + Redis reachable |

### Liveness — `GET /health`

Always returns `200` if the HTTP server is responding.

```json
{"status": "ok"}
```

### Readiness — `GET /health/ready`

Runs dependency checks and returns aggregate status plus per-check detail.

**All checks pass (`200`):**

```json
{
  "status": "ok",
  "checks": {
    "postgres": {"status": "ok"},
    "redis": {"status": "ok"}
  }
}
```

**Any check fails (`503`):**

```json
{
  "status": "error",
  "checks": {
    "postgres": {"status": "error", "detail": "connection refused"},
    "redis": {"status": "ok"}
  }
}
```

## What is checked

| Dependency | Check |
|------------|-------|
| Postgres | `SELECT 1` via SQLAlchemy session |
| Redis | `PING` via async Redis client |

Redis URL resolution order:

1. `CELERY_BROKER_URL` — if it starts with `redis://` or `rediss://`
2. `CATALOG_CACHE_REDIS_URL`
3. `WATCH_PARTY_REDIS_URL`

## What is not checked

- Celery worker process (only Redis broker connectivity)
- External APIs (Kinopoisk, Telegram, TMDB, etc.)
- RustFS / S3-compatible object storage
- Frontend or other compose services

## Docker

The backend image installs `curl` in the `base` stage (`backend/Dockerfile`). Both `dev` and `prod` image stages define a `HEALTHCHECK` that runs:

```text
curl -fsS "http://127.0.0.1:${PORT:-8000}/health/ready"
```

The probe uses the container `PORT` environment variable (production sets `PORT=6949` for Caddy; default `8000` in dev and settings).

### Docker Compose

The `backend` service in `docker-compose.yml` and `docker-compose.prod.yml` uses the same curl-based probe:

- `test`: `CMD-SHELL curl -fsS "http://127.0.0.1:${PORT:-8000}/health/ready"`
- `interval`: 30s
- `timeout`: 5s
- `retries`: 3
- `start_period`: 20s

Compose marks the container healthy only when readiness returns `200` (Postgres and Redis up).

### Celery worker

The `celery-worker` service uses a **broker/worker ping**, not HTTP. Compose overrides the image `HEALTHCHECK` (which targets the API readiness URL) with:

```text
celery -A celery_app inspect ping -d celery@$HOSTNAME --timeout 5
```

In `docker-compose.yml` and `docker-compose.prod.yml`:

- `test`: `CMD-SHELL` with the `inspect ping` command above (`$$HOSTNAME` in compose files)
- `interval`: 30s
- `timeout`: 10s
- `retries`: 3
- `start_period`: 40s

The worker is healthy when Celery can reach the broker and the named worker responds to `inspect ping`.

## Tests

- Integration: `backend/src/tests/integration/api/test_health_routes.py`
- Unit: `backend/src/tests/unit/services/health/test_check_backend_readiness.py`
