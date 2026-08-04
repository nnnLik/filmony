# TMDB film integration — progress

Status: **completed**

## Done

- Film model + migration for TMDB snapshots and crosswalk ids
- TMDB provider layer (find, search, movie+credits)
- SyncFilmFromTmdbService with gamification mapping
- Resolve uses TMDB instead of KP staff/sequels (saves 2 KP calls/card)
- Franchise labels for `tmdb_collection:{id}`
- Backfill + compare management scripts
- Tests: provider, sync, franchise label, backfill, resolve API mocks
- Migration applied in dev Docker; ruff clean

## Prod next (manual)

1. Set `TMDB_*` in `vars/.env.production` (keys from secure channel — **not git**)
2. Deploy + `alembic upgrade head`
3. `manage_compare_kp_tmdb_metadata.py --limit 50 --allow-kp-imdb-lookup`
4. `ALLOW_KP_IMDB_LOOKUP=1 make backfill-film-tmdb-metadata` (rated-first)
