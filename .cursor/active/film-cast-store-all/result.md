# film-cast-store-all — result

Status: **complete**

## Implemented

- Alembic migration widens `film_actor.billing_order` check constraint to `>= 1` only (no upper bound)
- `parse_top_actors` returns every Kinopoisk `ACTOR` staff row with a name, preserving billing order
- `EnsureFilmCastService.execute(..., force=False)` unchanged for create-card path (skip if cast exists)
- `EnsureFilmCastService.execute(..., force=True)` deletes existing `film_actor` rows for the film and re-persists full cast; persons upserted by `kinopoisk_id` (no duplicates)
- `manage_backfill_film_cast --force` re-syncs films that already have cast rows

## Changed files

### Backend
- `backend/src/migrations/versions/d2e3f4a5b6c7_film_actor_unlimited_billing.py`
- `backend/src/models/film_actor.py`
- `backend/src/services/cast/parse_top_actors.py`
- `backend/src/services/cast/ensure_film_cast.py`
- `backend/src/manage_backfill_film_cast.py`

### Tests
- `backend/src/tests/unit/services/cast/test_parse_top_actors.py`
- `backend/src/tests/integration/services/cast/test_ensure_film_cast.py`
- `backend/src/tests/integration/scripts/test_manage_backfill_film_cast.py`

## Verification

```bash
make backend-test-one target=src/tests/unit/services/cast/test_parse_top_actors.py
make backend-test-one target=src/tests/integration/services/cast/test_ensure_film_cast.py
make backend-test-one target=src/tests/integration/scripts/test_manage_backfill_film_cast.py
```

14 passed (3 cast test files).

## Known limitations

- Films synced before this release still have at most 10 `film_actor` rows until re-synced
- Production re-sync deferred: run `manage_backfill_film_cast --force` after release (user will request later)
- Cast source remains Kinopoisk staff API (`ACTOR` profession only); no frontend changes in this feature

## Next steps

- Deploy migration (`alembic upgrade head`)
- Schedule `manage_backfill_film_cast --force` for production when requested
