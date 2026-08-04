# Action log fragment

**Timestamp:** 2026-05-13T171000Z

**Feature slug:** abstract-user-cards

**Action type:** code

## Summary

Added nullable user-facing columns on `movie_card`: `display_title`, `display_cover_url`, `display_summary`, `source_url`. New Alembic revision `w3x4y5z6a012` (after `u1v2w3x4y890`) adds columns and backfills from `film` where `movie_card.film_id` matches (`title`, `poster_url`, `COALESCE(short_description, description)`). Downgrade drops the four columns. Extended model schema tests.

## Files

- `backend/src/models/movie_card.py`
- `backend/src/migrations/versions/w3x4y5z6a012_movie_card_user_display_fields.py`
- `backend/src/tests/models/test_movie_card_catalog_schema.py`
- `.cursor/active/abstract-user-cards/progress.md`
- `.cursor/memory/logs/action-log.md`
- `.cursor/memory/logs/2026-05-13T171000Z-abstract-user-cards-code.md`

## Verification

- `docker compose -f docker-compose.yml exec -w /opt/app backend pytest src/tests/models/test_movie_card_catalog_schema.py -v` — 6 passed
- `docker compose -f docker-compose.yml exec -w /opt/app backend alembic upgrade head` — applied `u1v2w3x4y890 -> w3x4y5z6a012`
- `docker compose -f docker-compose.yml exec -w /opt/app backend alembic downgrade -1` then `alembic upgrade head` — OK
