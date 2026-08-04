# TMDB film integration — result

Status: **completed**

## Implemented

- **TMDB provider** (`backend/src/providers/tmdb/`): find by IMDB, title search fallback, movie detail with `append_to_response=credits,external_ids`
- **SyncFilmFromTmdbService**: persists full JSON snapshot + maps `countries`, `primary_director_name`, `primary_director_tmdb_id`, `franchise_key` (`tmdb_collection:*` or singleton `kp_franchise:*`)
- **No overwrite** of existing `primary_director_kinopoisk_id` or `kp_franchise:*` keys (unless `--force-overwrite-gamification` for non-franchise fields)
- **Resolve path** uses TMDB enrichment; KP staff only when `ENRICH_KP_DIRECTOR_ID=true`
- **Scripts**: `manage_backfill_film_tmdb_metadata.py`, `manage_compare_kp_tmdb_metadata.py`
- **Makefile**: `backfill-film-tmdb-metadata`

## Changed files (main)

- `backend/src/models/film.py`
- `backend/src/migrations/versions/n6o7p8q9r012_film_tmdb_metadata.py`
- `backend/src/conf/settings.py`
- `backend/src/providers/tmdb/*`
- `backend/src/services/tmdb/sync_film_from_tmdb.py`
- `backend/src/services/kinopoisk/client.py`, `resolve_kinopoisk_film.py`
- `backend/src/services/franchises/franchise_label.py`
- `backend/src/manage_backfill_film_tmdb_metadata.py`
- `backend/src/manage_compare_kp_tmdb_metadata.py`
- `backend/src/api/films/schemas.py`, `routes.py`
- Tests under `backend/src/tests/providers/`, `services/tmdb/`, `scripts/`

## Verification

```bash
docker exec -w /opt/app filmony-backend alembic upgrade head
docker exec -w /opt/app/src filmony-backend ruff check --config /opt/app/pyproject.toml .
make backend-test-one target=src/tests/providers/test_tmdb_movie_dto.py
make backend-test-one target=src/tests/services/tmdb/test_sync_film_from_tmdb.py
make backend-test-one target=src/tests/scripts/test_manage_backfill_film_tmdb_metadata.py
```

All passed.

## Prod rollout

1. Add to **`vars/.env.production`** (not committed):

```bash
TMDB_API_KEY=<your-api-key>
TMDB_API_READ_ACCESS_TOKEN=<JWT read access token>
TMDB_API_BASE_URL=https://api.themoviedb.org/3
TMDB_IMAGE_BASE_URL=https://image.tmdb.org/t/p/w500
TMDB_LANGUAGE=ru-RU
ENRICH_KP_DIRECTOR_ID=false
```

2. Deploy + migrate + restart backend
3. Compare KP vs TMDB on enriched subset:

```bash
docker exec -w /opt/app filmony-backend python src/manage_compare_kp_tmdb_metadata.py --limit 50 --allow-kp-imdb-lookup
```

4. Backfill rated films (~370):

```bash
ALLOW_KP_IMDB_LOOKUP=1 make backfill-film-tmdb-metadata
```

5. Re-run prod diagnostic — expect rated-without-director → ~0 names

## Known limitations

- Director **page links** still require `primary_director_kinopoisk_id` (v1); TMDB fills name + `primary_director_tmdb_id`
- TV/serial titles: TMDB movie-only in v1
- Franchise clustering differs: TMDB collections vs KP sequels
