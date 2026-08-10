# film-cast-store-all — progress

**Status:** completed

## 2026-08-10

- Feature scaffolding created (`feature.md`, `plan.md`, `progress.md`)
- HOT updated: `film-cast-store-all` listed as in_progress #1
- Phase 1 — Migration: dropped upper bound on `ck_film_actor_billing_order_range` (`billing_order >= 1`)
- Phase 2 — Parse: removed `MAX_TOP_ACTORS` cap; all `ACTOR` staff rows with names returned
- Phase 3 — `EnsureFilmCastService`: added `force` parameter; delete-and-replace cast when `force=True`
- Phase 4 — Backfill CLI: `--force` flag to re-sync films with existing partial cast
- Phase 5 — Call sites unchanged (`force=False` default on create-card path)
- Phase 6 — Tests: unit + integration for unlimited cast, force refresh, person dedupe, backfill `--force`
- Phase 7 — Closeout: `result.md`, `docs/features/film-cast-store-all.md`, action log, HOT `recent_completed`
