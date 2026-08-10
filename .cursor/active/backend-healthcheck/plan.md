# backend-healthcheck — active plan

**Status:** in_progress  
**Started:** 2026-08-11  
**Slug:** `backend-healthcheck`

## Step 1 — Liveness route

- [ ] Add `GET /health` route (public, no auth)
- [ ] Return `200` with `{"status":"ok"}`; no DB/Redis calls

## Step 2 — Readiness service + route

- [ ] Add readiness check service (Postgres `SELECT 1`, Redis `PING` via `CELERY_BROKER_URL`)
- [ ] Add `GET /health/ready` route (public, no auth)
- [ ] Response JSON includes per-check status (`postgres`, `redis`)
- [ ] Return `200` when all checks pass; `503` when any required check fails

## Step 3 — Wire routes into app

- [ ] Register health routes on the FastAPI app (alongside existing public routes)
- [ ] Confirm no conflict with existing `GET /` and `GET /api/hello`

## Step 4 — Integration tests

- [ ] Add `backend/src/tests/integration/api/test_health_routes.py`
- [ ] Cover `GET /health` — always `200`, body `{"status":"ok"}`
- [ ] Cover `GET /health/ready` — `200` when Postgres + Redis are up
- [ ] Cover readiness failure path (e.g. mocked/broken dependency) where feasible

## Step 5 — Docker Compose healthchecks

- [ ] Add `healthcheck` to `backend` service in `docker-compose.yml` (probe `/health/ready`)
- [ ] Add same `healthcheck` to `backend` service in `docker-compose.prod.yml`
- [ ] Use sensible `interval`, `timeout`, `retries`, `start_period`

## Step 6 — Verification

- [ ] `make backend-test-one target=src/tests/integration/api/test_health_routes.py` — pass
- [ ] `docker compose up` — backend container reports healthy once deps are ready

## Closeout

- [ ] Write `.cursor/active/backend-healthcheck/result.md`
- [ ] Publish `docs/features/backend-healthcheck.md`
- [ ] Update HOT and append action-log fragment
