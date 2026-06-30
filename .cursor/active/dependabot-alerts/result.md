# Dependabot Alerts — Result

status: complete

## Implemented

- Frontend npm dependencies updated via `npm update` + `npm audit fix`.
- Added npm override for `valibot@^1.2.0` to fix transitive `@telegram-apps/*` advisories without major SDK downgrade.
- Backend `pyproject.toml` bumped vulnerable direct deps and pinned safe transitive minimums.
- Regenerated `backend/uv.lock` and rebuilt backend Docker image.
- Published `docs/features/dependabot-alerts.md` and closed the planning artifacts.

## Changed files

- `frontend/package.json`
- `frontend/package-lock.json`
- `backend/pyproject.toml`
- `backend/uv.lock`
- `docs/features/dependabot-alerts.md`
- `.cursor/active/dependabot-alerts/progress.md`
- `.cursor/active/dependabot-alerts/result.md`

## Verification

| Check | Command | Result |
|-------|---------|--------|
| Frontend audit | `cd frontend && npm audit` | 0 vulnerabilities |
| Frontend lint | `cd frontend && npm run lint` | pass |
| Frontend build | `cd frontend && npm run build` | pass |
| Backend tests | `docker exec -w /opt/app/src filmony-backend pytest` | 306 passed |
| Backend lint | `docker exec -w /opt/app/src filmony-backend ruff check …` | 2 pre-existing PLR0915 (watchlist), unrelated |

## Known limitations

- GitHub Dependabot alert UI may still show open items until dependency files are merged and Dependabot re-scans.
- `valibot` fix uses npm `overrides`; if `@telegram-apps/*` breaks on future releases, revisit override.

## Next steps

- Merge changes and wait for Dependabot rescan.
