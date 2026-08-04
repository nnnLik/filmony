# 2026-08-04T160000Z — tmdb-film-integration closeout

- **Feature:** `tmdb-film-integration`
- **Action:** TMDB provider, Film snapshot columns, SyncFilmFromTmdbService, resolve/backfill/compare scripts
- **Verification:** ruff clean; pytest on provider/sync/backfill/franchise/resolve mocks

## Files

- `backend/src/providers/tmdb/`
- `backend/src/services/tmdb/sync_film_from_tmdb.py`
- `backend/src/migrations/versions/n6o7p8q9r012_film_tmdb_metadata.py`
- `backend/src/manage_backfill_film_tmdb_metadata.py`
- `backend/src/manage_compare_kp_tmdb_metadata.py`
- `docs/features/tmdb-film-integration.md`
