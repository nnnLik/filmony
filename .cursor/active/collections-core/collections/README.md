# Collections pipeline workspace

Working artifacts and scripts for Letterboxd lists and Oscar ceremony collections.
Git-tracked **production manifests** live in `backend/src/data/curated/`.

> **Legacy redirect:** `.cursor/active/collections-core/data/` is deprecated — see `data/README.md` for the old→new path map. Always use this `collections/` tree as the working root.

## Layout

| Path | Purpose |
|------|---------|
| `_tools/` | Shared pipeline scripts (`scrape_letterboxd_list.py`, `map_lb_kp.py`, `build_lb_kp_full.py`) |
| `{slug}/intermediate/` | Raw scrape, KP mapping, reports, `ru_aliases.json` |
| `{slug}/letterboxd_{slug}_kinopoisk_full.json` | Enriched manifest (working copy before promote) |
| `oscars/` | Oscar-specific mapper + meta; year files in `oscars/intermediate/` |

### Collections

| Slug (LIST_CONFIGS key) | Collection slug (DB) | Notes |
|-------------------------|----------------------|-------|
| `horror_250` | `letterboxd-horror-250` | Letterboxd Horror 250 |
| `samurai_100` | `letterboxd-samurai-100` | Letterboxd Samurai 100 |
| `top_500` | `letterboxd-top-500` | Reference / evergreen seed source |
| `oscars/` | `oscars-{year}` | Oscar best-picture nominees 2020–2026 |

Use short underscore keys (`horror_250`) for `--slug` and `LIST_CONFIGS`; hyphenated slugs are for the seeded `Collection.slug`.

## Running scripts

**Pitfalls:**

- `.cursor/` is **not** mounted in the backend Docker image — pipeline tools run on the **host** via backend venv, not inside the container.
- Host Python often lacks `httpx`; always use `uv run` from `backend/`.
- Load Kinopoisk credentials from `vars/.env.development.local` before running.

```bash
cd backend
set -a && source ../vars/.env.development.local && set +a

uv run python ../.cursor/active/collections-core/collections/_tools/scrape_letterboxd_list.py --help
uv run python ../.cursor/active/collections-core/collections/_tools/map_lb_kp.py --help
uv run python ../.cursor/active/collections-core/collections/_tools/build_lb_kp_full.py --help
```

Oscar mapper (under `collections/oscars/`):

```bash
uv run python ../.cursor/active/collections-core/collections/oscars/map_oscar_kp.py --help
```

**Backend seed / backfill** (inside Docker — compose **service** name `backend`, container `filmony-backend`):

```bash
docker compose exec -w /opt/app backend python src/manage_seed_letterboxd_list_full.py --list horror_250 --dry-run
```

## Promote to curated

Copy resolved `*_kinopoisk_full.json` (or Oscar `*_kinopoisk.json`) into:

- `backend/src/data/curated/letterboxd_{slug}_kinopoisk_full.json`
- `backend/src/data/curated/oscars/oscars_{year}_kinopoisk.json`

Then register in `manage_seed_letterboxd_list_full.py` (`LIST_CONFIGS`) or run `manage_seed_oscars.py` / `manage_seed_letterboxd_top_500.py`.

**After prod seed:** always run `manage_backfill_collection_progress.py` (mandatory).

Full pipeline skill: `.cursor/skills/letterboxd-list-to-collection/SKILL.md`  
Prod runbook: `../PROD_SEED.md`
