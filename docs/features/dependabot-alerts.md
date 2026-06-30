# Dependabot Alerts Fix

## Summary

Security dependency updates for frontend (npm) and backend (uv/Python) to resolve Dependabot advisories using minor/patch bumps only.

## Frontend

- Ran `npm update` and `npm audit fix`.
- Added override: `"valibot": "^1.2.0"` to patch transitive ReDoS in `@telegram-apps/*` chain without downgrading SDK majors.
- Result: `npm audit` reports **0 vulnerabilities**.

## Backend

Updated in `backend/pyproject.toml`:

| Package | From | To |
|---------|------|-----|
| pydantic-settings | 2.14.0 | 2.14.2 |
| pyjwt | 2.12.1 | 2.13.0 |
| python-multipart | 0.0.28 | 0.0.31 |
| starlette | 1.0.0 (transitive) | ≥1.3.1 |
| urllib3 | 2.6.3 (transitive) | ≥2.7.0 |
| idna | 3.13 (transitive) | ≥3.15 |

Regenerated `backend/uv.lock`; rebuilt backend container.

## Verification

```bash
cd frontend && npm audit && npm run lint && npm run build
docker compose build backend && docker compose up -d backend
docker exec -w /opt/app/src filmony-backend pytest
```

## Rollback

Revert `frontend/package.json`, `frontend/package-lock.json`, `backend/pyproject.toml`, `backend/uv.lock` and rebuild backend image.
