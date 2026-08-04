# monthly-recap — result

Status: **done**

## Implemented
- `BuildMonthlyRecapService` — cards, top-3, stamps, marathons, peak day, genre of month (UTC).
- `GET /api/me/recap/{year}/{month}`, `GET /api/me/recap/latest`.
- `monthly_recap_nudge_state` + `SendMonthlyRecapTelegramNudgeService` + Celery `send_monthly_recap_nudges`.
- Deep link `mr{year}-{month}` in `mini_app_link.py` and frontend `parseMiniAppRecapStartParam`.
- `MonthlyRecapPage`, routes, ProfilePage dismissible banner.

## Verification
- `make backend-test-one target=src/tests/api/test_monthly_recap_routes.py` — 4 passed
- `make backend-test-one target=src/tests/tasks/test_monthly_recap_task.py` — 1 passed
- `cd frontend && npm run lint && npm run build`
