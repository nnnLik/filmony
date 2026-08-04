# TMDB film integration

## Overview

Secondary enrichment source for `Film` rows: full TMDB metadata stored locally, gamification fields filled without Kinopoisk staff/sequels API calls (500/day quota).

Kinopoisk remains catalog identity (`kinopoisk_id`).

## Data model

| Column | Purpose |
|--------|---------|
| `imdb_id` | Crosswalk KP → TMDB |
| `tmdb_id` | TMDB movie id |
| `primary_director_tmdb_id` | TMDB person id |
| `tmdb_detail_snapshot_json` | Full API response (incl. credits append) |
| `tmdb_synced_at` | Last sync timestamp |

## Enrichment flow

1. Resolve `imdb_id` (from KP resolve, DB, or optional KP `get_film` in backfill)
2. `GET /find/{imdb_id}?external_source=imdb_id` or title/year search
3. `GET /movie/{id}?append_to_response=credits,external_ids`
4. Map countries, director name, franchise key

**Franchise keys:** `tmdb_collection:{id}` when collection exists; else `kp_franchise:{kinopoisk_id}`.

**Preserve KP data:** existing `primary_director_kinopoisk_id` and `kp_franchise:*` not overwritten by default.

## Ops

```bash
# Compare KP-enriched films vs TMDB (before mass backfill)
python src/manage_compare_kp_tmdb_metadata.py --limit 50 --allow-kp-imdb-lookup

# Backfill rated films only (~741 on prod; ignores KP search cache orphans)
docker exec -w /opt/app filmony-backend python src/manage_backfill_film_tmdb_metadata.py

# Verify rated-film coverage
docker exec -w /opt/app filmony-backend python src/manage_diagnose_film_tmdb_metadata.py
```

## Env

```
TMDB_API_KEY=
TMDB_API_READ_ACCESS_TOKEN=
TMDB_API_BASE_URL=https://api.themoviedb.org/3
TMDB_IMAGE_BASE_URL=https://image.tmdb.org/t/p/w500
TMDB_LANGUAGE=ru-RU
ENRICH_KP_DIRECTOR_ID=false
```

Prod: `vars/.env.production` only — never commit keys.

## API

`FilmResponse` exposes optional `imdb_id`, `tmdb_id`, `primary_director_tmdb_id`.

## Tests

- `backend/src/tests/providers/test_tmdb_movie_dto.py`
- `backend/src/tests/services/tmdb/test_sync_film_from_tmdb.py`
- `backend/src/tests/scripts/test_manage_backfill_film_tmdb_metadata.py`
