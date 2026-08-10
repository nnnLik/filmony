# film-cast-store-all

## Summary
Store full Kinopoisk actor cast per film (not only first 10). Keep person dedupe by kinopoisk_id. Support forced re-sync for films that already have partial cast.

## Acceptance criteria
- Parse/persist all `ACTOR` staff rows with names (no MAX_TOP_ACTORS=10 cap).
- DB allows billing_order > 10 (`ck_film_actor_billing_order_range` dropped or widened to >=1 only).
- Person upsert by `kinopoisk_id` never creates duplicates.
- `EnsureFilmCastService.execute(..., force=False)` remains skip-if-cast-exists for create-card path.
- `force=True` replaces film_actor rows for that film and re-upserts persons (no person duplicates).
- Backfill CLI supports `--force` to re-sync films that already have cast.
- Unit/integration tests cover unlimited cast + force refresh + person reuse.
- Docker pytest for touched tests passes.
