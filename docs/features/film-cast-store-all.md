# Film cast: store full actor list

Extends [actor cast profile stats](./actor-cast-profile-stats.md) to persist the **full** Kinopoisk `ACTOR` cast per film instead of the first 10 billing-order entries. Adds a forced re-sync path for films that already have partial cast from the earlier top-10 implementation.

## Summary

| Before | After |
|--------|-------|
| Top 10 `ACTOR` rows per film | All `ACTOR` staff rows with names |
| `billing_order` capped at 10 (DB check) | `billing_order >= 1` only |
| Backfill skips films with any cast | `--force` replaces cast for selected films |

Person dedupe by `kinopoisk_id` is unchanged: one `person` row shared across films.

## Behavior

### Parse (`parse_top_actors`)

- Filters Kinopoisk staff to `staff_profession == 'ACTOR'` with a non-empty name
- Assigns `billing_order` 1..N in Kinopoisk staff order
- No row-count cap

### Ensure (`EnsureFilmCastService`)

- **`force=False` (default):** idempotent skip when any `film_actor` row exists for the film — used by rated card create/upgrade
- **`force=True`:** deletes all `film_actor` rows for the film, fetches staff, parses full cast, upserts persons by `kinopoisk_id`, inserts new links
- Kinopoisk transport errors are logged and swallowed (card create path is not blocked)

### Backfill CLI

```bash
# New films only (default)
python -m manage_backfill_film_cast --dry-run
python -m manage_backfill_film_cast --sleep 0.5

# Re-sync films that already have cast (e.g. after deploy)
python -m manage_backfill_film_cast --force --dry-run
python -m manage_backfill_film_cast --force --sleep 0.5
```

`--force` includes films with existing `film_actor` rows and passes `force=True` into `EnsureFilmCastService`.

## Migration

Revision `d2e3f4a5b6c7`: replaces `ck_film_actor_billing_order_range` with `billing_order >= 1` (drops `<= 10` upper bound). `uq_film_actor_film_billing_order` unchanged.

```bash
alembic upgrade head
```

## Person dedupe

`_upsert_person` in `EnsureFilmCastService` looks up by `kinopoisk_id` before insert. The same actor appearing on multiple films or across force re-syncs updates name/photo on the existing `person` row — no duplicate persons.

## Key files

- `backend/src/services/cast/parse_top_actors.py`
- `backend/src/services/cast/ensure_film_cast.py`
- `backend/src/manage_backfill_film_cast.py`
- `backend/src/models/film_actor.py`
- `backend/src/migrations/versions/d2e3f4a5b6c7_film_actor_unlimited_billing.py`

## Operations (post-release)

1. Run migration in each environment
2. When ready, run `manage_backfill_film_cast --force` to refresh historical films that still have only 10 cast rows

## Verification

```bash
make backend-test-one target=src/tests/unit/services/cast/test_parse_top_actors.py
make backend-test-one target=src/tests/integration/services/cast/test_ensure_film_cast.py
make backend-test-one target=src/tests/integration/scripts/test_manage_backfill_film_cast.py
```
