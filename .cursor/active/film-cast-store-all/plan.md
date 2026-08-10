# Plan: film-cast-store-all

Store the full Kinopoisk `ACTOR` cast per film (remove top-10 cap), widen DB constraints, and add `force` refresh for films that already have partial cast. Builds on `actor-cast-profile-stats` (`person`, `film_actor`, `EnsureFilmCastService`, `manage_backfill_film_cast`).

## Phase 1 — Migration: billing_order constraint

**Goal:** Allow `billing_order > 10` while keeping `billing_order >= 1` and `UNIQUE (film_id, billing_order)`.

1. New Alembic revision under `backend/src/migrations/versions/`.
2. `op.drop_constraint('ck_film_actor_billing_order_range', 'film_actor', type_='check')`.
3. Add replacement check: `billing_order >= 1` only (no upper bound), or drop upper bound in model `CheckConstraint` if mirrored in `models/film_actor.py`.
4. Verify `uq_film_actor_film_billing_order` remains unchanged.
5. Run migration in Docker (`make migrate` or project equivalent).

**Files:** migration revision, optionally `backend/src/models/film_actor.py` if constraint is declared on model.

## Phase 2 — Parse: remove MAX_TOP_ACTORS cap

**Goal:** `parse_top_actors` returns every `ACTOR` staff row with a name, preserving Kinopoisk order.

1. In `backend/src/services/cast/parse_top_actors.py`:
   - Remove `MAX_TOP_ACTORS = 10` and the `billing_order > MAX_TOP_ACTORS` early break/skip.
   - Keep filters: `staff_profession == 'ACTOR'`, require non-empty name.
   - Preserve `billing_order` from staff order (1-based index as today).
2. Update module docstring / `ParsedTopActor` comments if they mention “top 10”.
3. Export cleanup in `backend/src/services/cast/__init__.py` if `MAX_TOP_ACTORS` was public.

**Unit tests** (`backend/src/tests/unit/services/cast/test_parse_top_actors.py`):
- Staff with 15+ ACTOR rows → all returned, order preserved.
- Remove or update tests that assert cap at 10.
- Empty / no ACTOR → empty tuple.

## Phase 3 — EnsureFilmCastService: `force` parameter

**Goal:** Default path stays idempotent skip; `force=True` replaces cast for one film.

1. Extend `execute(self, film_id: int, *, force: bool = False) -> None`.
2. When `force=False`: keep current early return if any `film_actor` row exists for `film_id`.
3. When `force=True`:
   - Skip the “existing cast” early return.
   - `DELETE FROM film_actor WHERE film_id = ?` (via session/DAO — prefer DAO method if added).
   - Fetch staff from Kinopoisk; `parse_top_actors(staff)`.
   - For each parsed actor: `_upsert_person` by `kinopoisk_id` (update name/poster if present).
   - Insert new `FilmActor` rows; `commit`.
4. KP transport errors: still swallow (do not fail card create path).
5. Update class docstring: full cast, not top-10.

**Optional DAO:** `FilmActorDAO.delete_for_film(film_id)` in `backend/src/daos/` if layering is preferred over inline delete in service.

**Integration tests** (`backend/src/tests/integration/services/cast/test_ensure_film_cast.py`):
- Film with 12+ mocked ACTOR staff → 12+ `film_actor` rows, `billing_order` 1..N.
- `force=False` on film with existing cast → no new rows (idempotent).
- `force=True` on film with 10 rows → after staff mock with 15 actors → 15 rows, old rows replaced.
- Same `kinopoisk_id` across two films → single `person` row (person reuse).

## Phase 4 — Backfill CLI: `--force`

**Goal:** Re-sync films that already have partial cast.

1. In `backend/src/manage_backfill_film_cast.py`:
   - Add `--force` flag (argparse).
   - When `--force`: include films that already have `film_actor` rows (not only missing cast).
   - Pass `force=True` into `EnsureFilmCastService.execute`.
   - Document in command help: replaces cast for selected films.
2. Update Makefile target `backfill-film-cast` if it documents flags.
3. Integration or script test if pattern exists for manage commands.

## Phase 5 — Call sites

1. `CreateUserCardService` / card hooks: keep `execute(film_id)` with default `force=False` — no behavior change on create-card path.
2. Grep for other `EnsureFilmCastService` callers; ensure they do not accidentally pass `force=True`.

## Phase 6 — Tests & verification

| Area | Path | Cases |
|------|------|-------|
| Parse | `tests/unit/services/cast/test_parse_top_actors.py` | >10 actors, order, no cap |
| Ensure | `tests/integration/services/cast/test_ensure_film_cast.py` | full persist, idempotent, force refresh, person dedupe |
| Backfill | integration or command test | `--force` selects films with existing cast |

Run in Docker:
- `make backend-test-one target=src/tests/unit/services/cast/test_parse_top_actors.py`
- `make backend-test-one target=src/tests/integration/services/cast/test_ensure_film_cast.py`
- `make backend-test` (full suite before closeout)

## Phase 7 — Docs & closeout

1. `docs/features/film-cast-store-all.md` — behavior, migration, CLI `--force`, limits (Kinopoisk staff API only).
2. `.cursor/active/film-cast-store-all/result.md` — changed files, verification commands, known limits.
3. Action-log fragment + HOT `recent_completed` on closeout.
4. Note in `docs/features/actor-cast-profile-stats.md` cross-link if top-10 wording remains.

## Dependencies / risks

- Kinopoisk staff payload size: full cast may be large; monitor row counts and API rate limits on backfill.
- `billing_order` uniqueness per film: force refresh must delete before insert to avoid unique violations.
- Profile stats / actor filters: verify UI still works with >10 actors per film (no frontend change expected unless capped in API).
