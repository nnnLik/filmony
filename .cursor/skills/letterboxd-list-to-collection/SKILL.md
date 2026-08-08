---
name: letterboxd-list-to-collection
description: >-
  Parses a Letterboxd list URL into JSON, enriches films via Kinopoisk (three-tier
  resolve: IMDb id, EN keyword/year, RU title fallback), builds a full curated
  manifest (film + director + actors), seeds the collection on prod, and backfills
  progress/cast/achievements.
  Use when the user pastes a letterboxd.com list URL, asks to import a Letterboxd
  top/list into Filmony, or runs the letterboxd-list-to-collection command.
---

# Letterboxd list → Filmony collection

Operational skill for the full pipeline. Invariants: [`.cursor/rules/letterboxd-list-collection-pipeline.mdc`](../../rules/letterboxd-list-collection-pipeline.mdc). JSON examples and CLI cheat sheet: [reference.md](reference.md).

## When to use

- User drops a URL like `https://letterboxd.com/official/list/top-250-horror-films/`
- User asks to build or seed a Filmony collection from a Letterboxd top/list
- User invokes the `letterboxd-list-to-collection` command

## Inputs to collect

| Input | Required | Notes |
|-------|----------|-------|
| Letterboxd list URL | Yes | Source for scrape |
| Slug key (`horror_250`, …) | Confirm before scrape | Short underscore key for `--slug` and `LIST_CONFIGS` |
| Collection slug, title, description | Confirm before prod | DB slug is hyphenated, e.g. `letterboxd-horror-250` |
| Prod seed now vs JSON only | Yes | Default: ask before prod apply |

## Known pitfalls / run environment

1. **Working root:** `.cursor/active/collections-core/collections/` — **not** `data/` (redirect only).
2. **Per-list layout:** `collections/<slug>/intermediate/` for scrape + map; `collections/<slug>/letterboxd_<slug>_kinopoisk_full.json` for working full manifest; promote to `backend/src/data/curated/`.
3. **Shared tools:** `collections/_tools/{scrape_letterboxd_list,map_lb_kp,build_lb_kp_full}.py`
4. **Runner:** host Python often lacks `httpx`; `.cursor` is **not** mounted in Docker. Always:

   ```bash
   cd backend
   set -a && source ../vars/.env.development.local && set +a
   uv run python ../.cursor/active/collections-core/collections/_tools/<script>.py ...
   ```

5. **Docker compose service name is `backend`** (container `filmony-backend`). Use `docker compose exec -w /opt/app backend …` for seed/backfill scripts.
6. **KP staff API:** use `GET /v1/staff?filmId=` — `GET /v2.2/films/{id}/staff` returns 400.
7. **Tier 3 RU:** pass `--ru-aliases collections/<slug>/intermediate/ru_aliases.json` (create/extend when TODOs remain). `match_method` = `keyword_ru`.
8. **Slug convention:** short keys like `horror_250`, `samurai_100` (`LIST_CONFIGS` keys). Collection slug `letterboxd-horror-250`.
9. **Always dry-run before prod**; confirm with user before prod apply.
10. **Progress backfill mandatory** after seed (`manage_backfill_collection_progress.py`).

## Stage checklist (copy and track)

```
- [ ] 1 Scrape Letterboxd → raw JSON + meta (collections/<slug>/intermediate/)
- [ ] 2 Verify scrape count vs list
- [ ] 3 Map → kinopoisk ids (imdbId → EN keyword/year → RU aliases)
- [ ] 4 Resolve TODOs / verify 0 missing kp ids (or explicit accepted gaps)
- [ ] 5 Build collections/<slug>/letterboxd_<slug>_kinopoisk_full.json
- [ ] 6 Promote to backend/src/data/curated/
- [ ] 7 Register LIST_CONFIGS in manage_seed_letterboxd_list_full.py
- [ ] 8 Prod dry-run seed
- [ ] 9 Prod apply seed (user confirmed)
- [ ] 10 seed-achievements (+ badges sync if relevant)
- [ ] 11 backfill cast / director metadata as needed
- [ ] 12 backfill collection progress (mandatory)
- [ ] 13 Verify DB counts
```

## Stage details

### 1–2 Scrape

- **Working dir:** `.cursor/active/collections-core/collections/<slug>/intermediate/`
- **Script:** `collections/_tools/scrape_letterboxd_list.py`
- **Raw item shape:** `{rank, name, year, letterboxd_uri}`
- **Outputs:** `letterboxd_<slug>.json`, `letterboxd_<slug>.meta.json` (`source_url`, `scraped_at`, `expected_count`, `actual_count`)
- **Verify:** `actual_count == expected_count`; fail closed on mismatch

```bash
cd backend
set -a && source ../vars/.env.development.local && set +a
uv run python ../.cursor/active/collections-core/collections/_tools/scrape_letterboxd_list.py \
  --url "https://letterboxd.com/official/list/top-250-horror-films/" \
  --slug horror_250 \
  --expected-count 250
```

### 3–4 Map KP ids

- **Script:** `collections/_tools/map_lb_kp.py`
- **Env:** `KINOPOISK_API_KEY`, optional `KINOPOISK_API_BASE_URL` (from `vars/.env.development.local`)
- **Resolve strategy (three tiers):**
  1. **Primary:** Letterboxd film page → IMDb `tt…` → `GET /v2.2/films?imdbId=`
  2. **Secondary:** `keyword` + `yearFrom`/`yearTo` on Letterboxd English title, with title-similarity scoring
  3. **Tertiary:** `--ru-aliases collections/<slug>/intermediate/ru_aliases.json` — KP keyword search per alias query → `match_method=keyword_ru`
- **Output fields:** `rank`, `letterboxd_name`, `year`, `letterboxd_uri`, `imdb_id`, `kinopoisk_id`, `match_method` (`imdbId`, `keyword`, `keyword_ru`)
- **Gate:** no `TODO` / null `kinopoisk_id` unless user explicitly accepts gaps

```bash
uv run python ../.cursor/active/collections-core/collections/_tools/map_lb_kp.py \
  --slug horror_250 \
  --ru-aliases ../.cursor/active/collections-core/collections/horror_250/intermediate/ru_aliases.json
```

Use `--resume` / `--only-todos` to reprocess unresolved rows after extending `ru_aliases.json`.

### 5 Full manifest

- **Script:** `collections/_tools/build_lb_kp_full.py`
- **Working path:** `collections/<slug>/letterboxd_<slug>_kinopoisk_full.json`
- **Each row:** mapping fields + `film` object aligned with `_create_film_from_embedded` fields: `kinopoisk_id`, `title`, `year`, `poster_url`, `genres`, `countries`, `short_description`, `description`, `imdb_id`
- **Staff:** `GET /v1/staff?filmId={id}` for `director` and top `actors[]` (DIRECTOR + ACTORS). **Do not** use `/v2.2/films/{id}/staff` (400).
- **Film detail:** `GET /v2.2/films/{id}`
- Current seed script persists `film` fields only; director/cast land in DB via post-seed backfills
- **Verify:** `len(full) == len(mapped with numeric kp ids)`; every row has `film.title` and `film.kinopoisk_id`

```bash
uv run python ../.cursor/active/collections-core/collections/_tools/build_lb_kp_full.py \
  --slug horror_250
```

### 6–7 Register for seed

1. Copy manifest to `backend/src/data/curated/letterboxd_<slug>_kinopoisk_full.json`
2. Update `backend/src/manage_seed_letterboxd_list_full.py`:
   - Add `LIST_CONFIGS` entry: key (`horror_250`), `slug` (`letterboxd-horror-250`), `title`, `description`, `manifest` path
   - Extend argparse `--list` choices and `all`

**Idempotent seed behavior:** create missing films by `kinopoisk_id`, skip existing, upsert `Collection` + `CollectionFilm` `sort_order` from `rank`.

### 8–13 Prod (homelab)

- SSH to homelab prod host (user's usual `homelab` alias — ask if unknown; do not invent credentials)
- Work inside compose service **`backend`**, workdir `/opt/app`
- **Confirm with user** before apply (not dry-run)

```bash
docker compose exec -w /opt/app backend \
  python src/manage_seed_letterboxd_list_full.py --list horror_250 --dry-run
# then without --dry-run (user confirmed)
```

After seed:

```bash
make seed-achievements
# optional: make sync-film-award-badges
make backfill-film-gamification-metadata   # DRY_RUN/LIMIT via Makefile env
make backfill-film-cast
docker compose exec -w /opt/app backend \
  python src/manage_backfill_collection_progress.py
```

**Progress backfill is mandatory** — users who already rated films in the new collection need updated watched counters / achievement progress.

**Cast / gamification backfill scope:** `make backfill-film-cast` and `make backfill-film-gamification-metadata` currently target only films with rated UserCards — not every newly seeded film. Unrated seeded films may lack director/cast in the DB until someone rates them or a broader backfill / `FORCE` path is used. The full manifest JSON still embeds `director` and `actors[]` for completeness.

**Runbook:** `.cursor/active/collections-core/PROD_SEED.md`

## Safety

- Always dry-run before prod apply; get explicit user confirmation before apply
- Do not force-push; do not mutate user ratings
- Seed must not reset user collection progress (use dedicated backfill)
- Pipeline tools on host (`uv run`); seed/backfill inside Docker (`backend` service)

## Additional resources

- [reference.md](reference.md) — JSON examples and CLI cheat sheet (`horror_250` end-to-end)
