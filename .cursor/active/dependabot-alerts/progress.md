status: in_progress

- Updated plan to focus on minor/patch dependency updates (npm + uv).
- Frontend: `npm update`, `npm audit fix`, added `valibot` override `^1.2.0` → **0 vulnerabilities**.
- Frontend verification: `npm run lint` ✅, `npm run build` ✅.
- Backend: bumped `pydantic-settings`, `pyjwt`, `python-multipart`, pinned `starlette`, `urllib3`, `idna`; regenerated `uv.lock`.
- Backend verification: `pytest` 306 passed ✅; `ruff check` has 2 pre-existing PLR0915 in watchlist service (unchanged by this work).
- Pending: `result.md`, `docs/features/dependabot-alerts.md`, action-log entry.
