# TMDB film integration — plan

## Steps

1. [x] Migration `n6o7p8q9r012`: `imdb_id`, `tmdb_id`, `primary_director_tmdb_id`, `tmdb_detail_snapshot_json`, `tmdb_synced_at`
2. [x] `TmdbSettings` + env vars
3. [x] `providers/tmdb/` transport + DTOs + mapping
4. [x] `SyncFilmFromTmdbService` with KP no-overwrite rules
5. [x] Resolve path: TMDB sync replaces KP staff/sequels; optional `ENRICH_KP_DIRECTOR_ID`
6. [x] `franchise_label` for `tmdb_collection:*`
7. [x] Scripts: backfill + compare + Makefile target
8. [x] API: `FilmResponse` optional TMDB fields
9. [x] Tests + docs

## Prod rollout

See `result.md` and `docs/features/tmdb-film-integration.md`.
