# Plan: film-award-badges

Oscar Best Picture nominee/winner badges as a Film-attached entity, synced from a curated dataset via `imdb_id`, exposed in API and film UI.

## Phase 0 — Artifacts & dataset

1. Finalize v1 scope: **Best Picture only** (nominee + winner).
2. Add curated dataset file, e.g. `backend/data/oscar_best_picture.json` (or `.csv`), schema:
   - `imdb_id: str` (e.g. `tt0137523`)
   - `ceremony_year: int` (e.g. `2000` for 72nd Academy Awards)
   - `kind: "nominee" | "winner"`
3. Document dataset provenance and update process in feature `result.md` / `docs/features/film-award-badges.md` at closeout.

## Phase 1 — Model & migration

### Model: `FilmAwardBadge`

Location: `backend/src/models/film_award_badge.py`

| Column | Type | Notes |
|--------|------|-------|
| `id` | PK int | autoincrement |
| `film_id` | FK → `film.id` | ON DELETE CASCADE |
| `kind` | str/enum | `oscar_best_picture_nominee`, `oscar_best_picture_winner` |
| `ceremony_year` | int | Academy ceremony year |
| `created_at` | datetime | optional audit |
| `updated_at` | datetime | optional audit |

Constraints:
- `UNIQUE (film_id, kind, ceremony_year)`
- Index on `film_id`
- **No** `collection_id` or collection FK

Export from `backend/src/models/__init__.py`.

### Migration

- Alembic revision under `backend/src/migrations/versions/`
- Create table + enum if used + unique constraint

## Phase 2 — DAO & services

### DAO: `FilmAwardBadgeDAO`

Location: `backend/src/daos/film_award_badge_dao.py`

- `upsert_badge(film_id, kind, ceremony_year) -> FilmAwardBadge`
- `list_by_film_id(film_id) -> list[FilmAwardBadge]` (ordered: year desc, winner before nominee)
- `delete_all_for_film(film_id)` — only if full-refresh strategy chosen; prefer upsert-only

### DTOs

Location: `backend/src/services/film_award_badges/dtos.py` (or colocated)

- `OscarDatasetRow` — parsed row from seed file
- `FilmAwardBadgeDTO` — service/API shape

### Services

1. **`LoadOscarBestPictureDatasetService`**
   - Reads versioned file from `backend/data/`
   - Validates rows; returns `list[OscarDatasetRow]`

2. **`SyncFilmAwardBadgesService`** (orchestrator)
   - `build()` wires DAO + film lookup
   - `execute(*, dry_run: bool = False) -> SyncFilmAwardBadgesResult`
   - For each dataset row: resolve `Film` by `imdb_id`; upsert badge; count matched/unmatched/skipped
   - Log unmatched `imdb_id` for backfill follow-up (TMDB enrichment)

3. Optional **`ListFilmAwardBadgesService`**
   - Thin read helper if not inlined in film fetch path

Pattern: `@dataclass`, `build()`, single `execute()`, typed nested errors.

## Phase 3 — Celery sync task

File: `backend/src/tasks/film_award_badges.py`

```python
"""Celery tasks: sync Oscar Best Picture badges from curated dataset.

Beat schedule (document only — configure externally):
    sync_film_award_badges: annually after Academy Awards ceremony
        (suggested: minute=0 hour=6 day_of_month=5 month_of_year=3 — first week of March UTC)
    Optional manual/on-demand: send_task after dataset file update any time.
"""
```

- `register_tasks(app)` pattern
- Task name: `tasks.film_award_badges.sync_film_award_badges`
- Calls `SyncFilmAwardBadgesService.build().execute()` via `_run_async_isolated` if async session needed (mirror `monthly_recap.py`)
- Register in `backend/src/celery_app.py` → `_register_all_tasks`

### One-off seed script (optional complement)

- `backend/src/scripts/manage_sync_film_award_badges.py` or Makefile target `make sync-film-award-badges`
- Invoked locally and in CI smoke; Celery task wraps same service

## Phase 4 — API

### Schemas: `backend/src/api/films/schemas.py`

```python
class FilmAwardBadgeResponse(BaseModel):
    kind: Literal['oscar_best_picture_nominee', 'oscar_best_picture_winner']
    ceremony_year: int

class FilmResponse(BaseModel):
    ...
    award_badges: list[FilmAwardBadgeResponse] = Field(default_factory=list)
```

Extend other film-summary schemas in scope (catalog community rated films, card film embed) if they duplicate `FilmResponse` fields — keep shapes consistent.

### Route wiring

- Film GET by id / resolve paths: load badges via DAO or eager load on film query
- Keep routes thin: map DTO → schema; no SQL in routes

## Phase 5 — Frontend

### Types

- Extend `Film` in `frontend/src/api/profileTypes.ts` (and any duplicate film types) with:

```typescript
export type FilmAwardBadge = {
  kind: 'oscar_best_picture_nominee' | 'oscar_best_picture_winner'
  ceremony_year: number
}
```

### Component: `FilmAwardBadgeStrip` (or single `FilmAwardBadge`)

Location: `frontend/src/components/films/FilmAwardBadgeStrip.tsx`

- Renders cup icon (lucide `Trophy` or project icon) + ceremony year
- Nominee: grey/muted cup; winner: gold/accent cup
- `aria-label` / `title` for accessibility — not text-only (icon + year visible)
- Compact mode prop for list rows vs detail header

### Surfaces (v1)

| Surface | Placement |
|---------|-----------|
| `FilmDetailPage` | Near title/year/meta row |
| `CatalogRatedFilmRow` | Compact strip under title or beside year |
| Feed/card film header | If film object includes `award_badges` in that path — wire when API available |

Follow TGUI + existing badge patterns (`ContrarianBadge`, `PlannedCardBadge`).

## Phase 6 — Tests

### Backend unit (`backend/src/tests/unit/`)

- Dataset parser / row validation
- Kind + year mapping logic
- Ordering comparator for badge lists

### Backend integration (`backend/src/tests/integration/`)

- `SyncFilmAwardBadgesService`: film with matching `imdb_id` gets badges; re-run idempotent
- Unmatched `imdb_id` skipped, no orphan badge rows
- Unique constraint violation handled by upsert
- Film API returns `award_badges` ordered correctly
- Celery task registration in `test_celery_app.py` (name present)

Fixtures: create `Film` rows with known `imdb_id` in integration tests.

### Frontend

- Vitest (if project pattern exists for similar components): render nominee vs winner variants
- Mandatory: `npm run lint && npm run build`

## Phase 7 — Docs & closeout

- `docs/features/film-award-badges.md`
- `.cursor/active/film-award-badges/result.md`
- Action-log fragment on closeout
- Update `.cursor/HOT.md` (`in_progress` → `recent_completed`)

## Dependency order

```
dataset → migration → DAO → sync service → Celery task → API → frontend → tests → docs
```

## Verification checklist

- [ ] `make backend-test-one target=src/tests/integration/services/film_award_badges/...`
- [ ] `make backend-test`
- [ ] `make sync-film-award-badges` (or documented script) populates badges on dev DB
- [ ] Manual: film with known Best Picture win shows gold cup + year on detail page
- [ ] `cd frontend && npm run lint && npm run build`

## Non-goals (explicit)

- Collection-owned badges or syncing from collection membership
- Achievement unlock hooks (`achievements-rarity-profile-pins`)
- Non–Best Picture Oscar categories in v1
