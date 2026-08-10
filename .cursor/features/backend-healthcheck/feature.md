# Feature: backend-healthcheck

## Scope

Add proper HTTP health probes for the Filmony backend (liveness + readiness). Today only `GET /` and `GET /api/hello` exist; they do not verify Postgres or Redis connectivity.

## Acceptance criteria

- [ ] `GET /health` — liveness probe, no dependency checks; returns `200` with `{"status":"ok"}`.
- [ ] `GET /health/ready` — readiness probe; checks Postgres (`SELECT 1`) and Redis (`PING` via `CELERY_BROKER_URL` / Redis URL); returns `200` when all checks pass, `503` when any required check fails; JSON includes per-check status.
- [ ] Both endpoints are public (no auth).
- [ ] Integration tests cover both endpoints (happy path and failure cases where feasible).
- [ ] `docker-compose.yml` and `docker-compose.prod.yml` backend service include a `healthcheck` hitting `/health/ready`.
- [ ] Closeout doc: `docs/features/backend-healthcheck.md`.

## Slug

`backend-healthcheck`
