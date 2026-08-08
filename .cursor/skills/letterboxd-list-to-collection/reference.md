# Letterboxd list → collection — reference

Companion to [SKILL.md](SKILL.md).

## Working root

`.cursor/active/collections-core/collections/` — per-list `intermediate/` + promoted curated manifests in `backend/src/data/curated/`.

Legacy `collections-core/data/` is a redirect only (see `data/README.md`).

## Example raw JSON item

From `collections/horror_250/intermediate/letterboxd_horror_250.json`:

```json
{
  "rank": 1,
  "name": "The Exorcist",
  "year": 1973,
  "letterboxd_uri": "https://letterboxd.com/film/the-exorcist/"
}
```

## Example meta file

From `collections/horror_250/intermediate/letterboxd_horror_250.meta.json`:

```json
{
  "source_url": "https://letterboxd.com/official/list/top-250-horror-films/",
  "scraped_at": "2026-08-08T00:05:21Z",
  "expected_count": 250,
  "actual_count": 250
}
```

## Kinopoisk resolve strategy (three tiers)

| Tier | Method | Status in `map_lb_kp.py` |
|------|--------|--------------------------|
| 1 — Primary | Letterboxd page → IMDb `tt…` → `GET /v2.2/films?imdbId=` | Implemented |
| 2 — Secondary | `keyword` + `yearFrom`/`yearTo` on Letterboxd English title | Implemented |
| 3 — Tertiary | `--ru-aliases` JSON → KP keyword/RU title + year | Implemented (`match_method=keyword_ru`) |

`match_method` values: `imdbId`, `keyword`, `keyword_ru`.

### RU aliases file shape

`collections/<slug>/intermediate/ru_aliases.json`:

```json
[
  {
    "imdb_id": "tt0063633",
    "letterboxd_name": "The Cremator",
    "year": 1969,
    "queries": ["Сжигатель трупов", "Spalovač mrtvol"]
  }
]
```

## Example mapping JSON item

From `collections/horror_250/intermediate/letterboxd_horror_250_kinopoisk.json`:

```json
{
  "rank": 1,
  "letterboxd_name": "The Exorcist",
  "year": 1973,
  "letterboxd_uri": "https://letterboxd.com/film/the-exorcist/",
  "imdb_id": "tt0070047",
  "kinopoisk_id": 491,
  "match_method": "imdbId"
}
```

## Example full manifest row

Pattern from `backend/src/data/curated/letterboxd_horror_250_kinopoisk_full.json`, with staff from `GET /v1/staff?filmId=`:

```json
{
  "rank": 1,
  "letterboxd_name": "The Exorcist",
  "year": 1973,
  "letterboxd_uri": "https://letterboxd.com/film/the-exorcist/",
  "imdb_id": "tt0070047",
  "kinopoisk_id": 491,
  "match_method": "imdbId",
  "film": {
    "kinopoisk_id": 491,
    "title": "Изгоняющий дьявола",
    "year": 1973,
    "poster_url": "https://kinopoiskapiunofficial.tech/images/posters/kp/491.jpg",
    "genres": ["ужасы"],
    "countries": ["США"],
    "short_description": "…",
    "description": "…",
    "imdb_id": "tt0070047"
  },
  "director": {
    "kinopoisk_staff_id": 224371,
    "name_ru": "Уильям Фридкин",
    "name_en": "William Friedkin"
  },
  "actors": [
    {
      "kinopoisk_staff_id": 30055,
      "name_ru": "Эллен Бёрстин",
      "name_en": "Ellen Burstyn",
      "order": 1
    }
  ]
}
```

**Staff API:** use `GET /v1/staff?filmId={id}`. Do **not** call `GET /v2.2/films/{id}/staff` (returns 400).

## Artifact directory table

| Artifact | Working (`collections/`) | Curated (git-tracked) |
|----------|--------------------------|------------------------|
| Raw scrape | `<slug>/intermediate/letterboxd_<slug>.json` | — |
| Scrape meta | `<slug>/intermediate/letterboxd_<slug>.meta.json` | — |
| RU aliases | `<slug>/intermediate/ru_aliases.json` | — |
| KP mapping | `<slug>/intermediate/letterboxd_<slug>_kinopoisk.json` | — |
| Mapping report | `<slug>/intermediate/letterboxd_<slug>_kinopoisk.txt` | — |
| Full manifest | `<slug>/letterboxd_<slug>_kinopoisk_full.json` | `backend/src/data/curated/letterboxd_<slug>_kinopoisk_full.json` |

Paths are relative to `.cursor/active/collections-core/collections/`.

## CLI cheat sheet — `horror_250` end-to-end

### Setup (every host run)

```bash
cd backend
set -a && source ../vars/.env.development.local && set +a
TOOLS=../.cursor/active/collections-core/collections/_tools
```

### 1. Scrape

```bash
uv run python $TOOLS/scrape_letterboxd_list.py \
  --url "https://letterboxd.com/official/list/top-250-horror-films/" \
  --slug horror_250 \
  --expected-count 250
```

Writes: `collections/horror_250/intermediate/letterboxd_horror_250.json` + `.meta.json`

### 2. Map → Kinopoisk

```bash
uv run python $TOOLS/map_lb_kp.py \
  --slug horror_250 \
  --ru-aliases ../.cursor/active/collections-core/collections/horror_250/intermediate/ru_aliases.json
```

Re-run with `--resume --only-todos` after extending `ru_aliases.json`.

### 3. Build full manifest

```bash
uv run python $TOOLS/build_lb_kp_full.py --slug horror_250
```

Writes: `collections/horror_250/letterboxd_horror_250_kinopoisk_full.json`

### 4. Promote + register

```bash
cp ../.cursor/active/collections-core/collections/horror_250/letterboxd_horror_250_kinopoisk_full.json \
   src/data/curated/
```

Add `horror_250` to `LIST_CONFIGS` in `manage_seed_letterboxd_list_full.py` (`slug`: `letterboxd-horror-250`).

### 5. Seed curated list (Docker / prod)

Compose **service** name: `backend` (container: `filmony-backend`).

```bash
# Dry-run (always first)
docker compose exec -w /opt/app backend \
  python src/manage_seed_letterboxd_list_full.py --list horror_250 --dry-run

# Apply (user confirmed)
docker compose exec -w /opt/app backend \
  python src/manage_seed_letterboxd_list_full.py --list horror_250

# All registered lists
docker compose exec -w /opt/app backend \
  python src/manage_seed_letterboxd_list_full.py --list all
```

`--limit N` and `--manifest PATH` override defaults for testing.

### 6. Post-seed backfills (Makefile targets exist)

```bash
DRY_RUN=1 make seed-achievements
make seed-achievements

DRY_RUN=1 make sync-film-award-badges   # optional
make sync-film-award-badges

DRY_RUN=1 LIMIT=50 make backfill-film-gamification-metadata
make backfill-film-gamification-metadata

DRY_RUN=1 LIMIT=50 make backfill-film-cast
make backfill-film-cast
```

**Limitation:** `backfill-film-cast` and `backfill-film-gamification-metadata` scope to films with rated UserCards. Newly seeded films with zero ratings may lack director/cast in the DB until rated or until a broader backfill / `FORCE` path is used. Full manifest JSON still stores `director` and `actors[]`; collection progress backfill remains mandatory regardless.

### 7. Collection progress backfill (mandatory)

```bash
docker compose exec -w /opt/app backend \
  python src/manage_backfill_collection_progress.py
```

Run **after every new collection seed** on prod.

### Makefile gaps

| Script | Makefile target | Workaround |
|--------|-----------------|------------|
| `manage_seed_letterboxd_list_full.py` | **none** (only `seed-letterboxd-top-500` for the legacy top-500 script) | `docker compose exec -w /opt/app backend python src/…` |
| `manage_backfill_collection_progress.py` | **none** | Same `docker compose exec` pattern |

### Prod runbook

See `.cursor/active/collections-core/PROD_SEED.md` for migrate → dry-run → apply → verify counts on homelab.
