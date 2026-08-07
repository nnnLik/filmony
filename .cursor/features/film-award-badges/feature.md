# Film Award Badges (Oscar)

## Metadata
- Feature slug: `film-award-badges`
- Status: `in_progress`
- Target area: fullstack (backend + frontend + Celery)
- Created at: 2026-08-07

## Problem

Films with notable Oscar history (Best Picture nominees and winners) carry no visible signal in Filmony. Users browsing catalog, film detail, or cards cannot tell at a glance that a title was nominated for or won an Academy Award. Collections may group themed sets of films, but they are editorial/curatorial surfaces — not a durable, queryable source of truth for award metadata tied to canonical `Film` rows.

TMDB and Kinopoisk integrations in this project do not expose reliable Oscar ceremony data; award facts must come from a curated external dataset keyed by `imdb_id`.

## Goal

Persist Oscar award badges as a **first-class entity attached to `Film`** and surface them in film API responses and film-card UI. Badges show ceremony year and kind (nominee vs winner) with a cup icon — not plain text-only labels.

## Scope

### In scope (v1)

- New persistence model `FilmAwardBadge` (or equivalent) with FK to `Film`; **not** owned by or derived from `Collection`.
- Badge kinds for v1:
  - **Oscar nominee** — grey cup icon + ceremony year
  - **Oscar winner** — gold cup icon + ceremony year
- **Category scope (v1): Best Picture only** — nominees and winners for the Academy Award for Best Picture.
- One film may hold **multiple badges** across different ceremony years (e.g. renominated or rare re-release edge cases handled as separate rows per ceremony year + kind).
- Curated Oscar dataset (static seed file or versioned JSON in repo) mapped to `Film` via `Film.imdb_id`; unmatched rows logged/skipped.
- Application services: seed/load dataset, sync/upsert badges idempotently, list badges for a film.
- Celery task(s) to re-sync badges after ceremony updates (winners marked post-ceremony); schedule documented in task module docstring; **host crontab external** — same pattern as `tasks/monthly_recap.py` and `docs/features/celery-redis-workers.md` (no Celery Beat in repo).
- API: include `award_badges` (or equivalent) on `FilmResponse`, collection film list items, and any film-summary DTOs used by catalog/community list endpoints in scope.
- Frontend: reusable badge component (icon + year) on film surfaces — at minimum `FilmDetailPage` header/meta and catalog rated-film row; compact variant for dense lists.
- Backend pytest (unit + integration) and frontend lint/build for touched files.

### Out of scope (v1)

- Badges for Oscar categories other than Best Picture (documented as v2: “any Oscar win/nominee” expansion).
- Other award bodies (Golden Globes, BAFTA, Cannes, etc.).
- User-facing badge collection, profile pins, or gamification unlocks — see sibling features below.
- Real-time external API polling (no Oscar API in project); updates are batch sync from curated dataset + manual dataset refresh.
- Achievements unlocked by badge presence — **badges do not unlock achievements in v1** unless a separate feature explicitly adds that rule.

### Open decision (documented)

| Option | Recommendation |
|--------|----------------|
| Best Picture only (v1) | **Adopt for MVP** — highest signal, smallest dataset, clearest UX (“Oscar Best Picture”). |
| All Oscar categories | Defer to v2+; requires larger dataset, denser UI, and category labeling. |
| “Any Oscar win” aggregate badge | Optional v2 shorthand badge kind if full category expansion is too noisy. |

**v1 acceptance criteria assume Best Picture only** unless implementation explicitly notes a scope change.

## Functional requirements

| ID | Requirement |
|----|-------------|
| FR-1 | Store award badges on `Film` via a dedicated table/model; collections may display the same films but must not own or author badge rows. |
| FR-2 | Support badge kinds `oscar_best_picture_nominee` and `oscar_best_picture_winner` with integer `ceremony_year` (year the Academy ceremony was held). |
| FR-3 | Enforce uniqueness per film + kind + ceremony year (idempotent upsert). |
| FR-4 | Map curated dataset entries to `Film` by `imdb_id`; skip or log when no matching film exists. |
| FR-5 | Expose badges on film read API(s) as ordered list (e.g. ceremony year desc, winners before nominees for same year if both ever apply). |
| FR-6 | Celery task `sync_film_award_badges` (name TBD in implementation) runs batch sync; module docstring documents suggested crontab (e.g. annually after Oscars + optional manual trigger). |
| FR-7 | Frontend styles the film **release year** with cup + border when a badge exists; **`ceremony_year` is not shown as the primary year** (only in tooltip/`aria-label`, e.g. “Оскар — лучший фильм (победитель), 2023 (церемония 2024)”). Film detail shows all badges; compact surfaces (feed, catalog, movie card, collection row) use `primaryFilmAwardBadge` only. |
| FR-8 | Management/seed path for initial load and dataset version bumps (script or service callable from Celery task). |

## Acceptance criteria

- [ ] Alembic migration creates `film_award_badge` (or agreed name) with FK to `film`, kind enum/string, `ceremony_year`, timestamps; unique constraint on `(film_id, kind, ceremony_year)`.
- [ ] Curated Best Picture Oscar dataset checked into repo (or documented path) with `imdb_id`, `ceremony_year`, `kind` (nominee/winner).
- [ ] `SyncFilmAwardBadgesService` (or equivalent) upserts badges from dataset; idempotent re-run; metrics/logging for unmatched `imdb_id`.
- [ ] Celery task registered via `register_tasks` pattern; docstring lists external schedule (e.g. `minute=0 hour=6 day_of_month=1 month_of_year=3` post-ceremony + on-demand); registered in `celery_app._register_all_tasks`.
- [ ] `FilmResponse` (and scoped list DTOs) include `award_badges: list[FilmAwardBadgeResponse]`.
- [ ] `OscarReleaseYearLabel` on `FilmDetailPage`, catalog film row, feed card, movie card detail, and collection film row (when `award_badges` present).
- [ ] Visual: grey cup + **release year** for nominee; gold cup + **release year** for winner — ceremony year in tooltip/a11y only, not as a separate pill.
- [ ] Multiple badges per film across years displayed correctly.
- [ ] Badges are independent of Collection entities; no Collection FK on badge model.
- [ ] No achievement/profile-pin side effects from badge sync in v1.
- [ ] Backend pytest: sync mapping, uniqueness, API serialization, unmatched imdb handling.
- [ ] `make backend-test` and `cd frontend && npm run lint && npm run build` pass for touched code.

## Constraints

- **Source of truth:** `Film` → badges; never Collection → badges.
- **Identity join:** `imdb_id` on `Film` (populated via TMDB/KP enrichment — see `tmdb-film-integration`); films without `imdb_id` cannot receive badges until enriched.
- **No TMDB/KP awards API** — curated dataset only.
- **Celery Beat not used** — external crontab invokes task or `send_task` from ops scripts.
- **Sibling features:** `collections-core` (curated lists), `achievements-rarity-profile-pins` (profile gamification) — badges may appear on films inside collections but do not drive collection membership or achievement unlocks in v1.

## References

- `backend/src/models/film.py` — `imdb_id` join key
- `backend/src/api/films/schemas.py` — `FilmResponse`
- `backend/src/tasks/monthly_recap.py` — Celery task + external schedule docstring pattern
- `docs/features/celery-redis-workers.md` — worker registration, no Beat
- `.cursor/features/tmdb-film-integration/feature.md` — IMDB crosswalk enrichment
- `.cursor/features/profile-gamification-stamps/feature.md` — separate badge/gamification patterns (contrarian, passport); not award badges
- `frontend/src/pages/FilmDetailPage.tsx`, `frontend/src/components/catalog/CatalogRatedFilmRow.tsx` — primary UI surfaces
- `frontend/src/components/gamification/ContrarianBadge.tsx` — compact badge component precedent
