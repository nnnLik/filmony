# Profile rating contrast stats

## Metadata
- Feature slug: `profile-rating-contrast-stats`
- Status: done
- Created at: 2026-08-15

## Goal
Show how user ratings differ from Kinopoisk and IMDb aggregates on profile Statistics → Overview.

## Acceptance criteria
- [x] Backend computes avg delta KP/IMDb, agreement %, contrarian count, biggest gap per rated card with external ratings.
- [x] `GET /api/users/:id/stats` includes `rating_contrast` with fields consumed by the frontend.
- [x] Overview shows section «Оценки vs КП и IMDb» with metrics and insight cards.
- [x] Empty state when no external ratings on user's films.
- [x] Unit + integration pytest coverage; frontend lint/build pass.
- [x] Ops script to backfill KP passport for rated films (`manage_backfill_film_kinopoisk_passport.py`).
