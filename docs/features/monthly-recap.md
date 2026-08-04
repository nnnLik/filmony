# Monthly Recap

Monthly in-app summary of rated-card activity plus a Telegram nudge on the 1st of each month.

## API

- `GET /api/me/recap/{year}/{month}` — auth required, own recap only (UTC month boundaries).
- `GET /api/me/recap/latest` — previous complete calendar month.

Response includes: `total_rated`, `average_rating`, `top_films`, `new_stamps`, `marathons_unlocked`, `peak_activity_date`, `genre_of_month`.

## Telegram

Celery task `tasks.monthly_recap.send_monthly_recap_nudges` (documented beat: 1st day 10:00 UTC). Short HTML message + deep link `startapp=mr{year}-{month}`.

Idempotency: `monthly_recap_nudge_state (user_id, year, month)`.

## Frontend

- Route: `/me/recap/:year/:month` and `/me/recap/latest`
- Profile banner when latest month has ratings; dismiss via `localStorage` key `recap_dismissed_{y}_{m}`.
