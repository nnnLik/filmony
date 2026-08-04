# Monthly Recap

## Metadata
- Feature slug: `monthly-recap`
- Status: done
- Target area: backend + frontend + Celery

## Scope
In-app monthly activity summary + Telegram nudge on the 1st with deep link to `/me/recap/{year}/{month}`.

## Acceptance criteria
- [x] `BuildMonthlyRecapService` aggregates rated cards in UTC month window
- [x] `GET /api/me/recap/{year}/{month}` and `GET /api/me/recap/latest`
- [x] `monthly_recap_nudge_state` migration + `send_monthly_recap_nudges` Celery task
- [x] Telegram nudge with `mr{year}-{month}` mini-app deep link
- [x] `MonthlyRecapPage`, route, ProfilePage banner with dismiss localStorage
- [x] pytest in `test_monthly_recap_routes.py`
