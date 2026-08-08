---
description: Letterboxd list → Kinopoisk JSON → prod Filmony collection + backfill
---

# Letterboxd list → collection

Follow the project skill `.cursor/skills/letterboxd-list-to-collection/SKILL.md` and rule `.cursor/rules/letterboxd-list-collection-pipeline.mdc`.

The user will provide (or has provided) a Letterboxd list URL, e.g. `https://letterboxd.com/official/list/top-250-horror-films/`.

**Working root:** `.cursor/active/collections-core/collections/` (not `data/`).  
**Host runner:** `cd backend && set -a && source ../vars/.env.development.local && set +a && uv run python ../.cursor/active/collections-core/collections/_tools/…`  
**Docker seed/backfill:** `docker compose exec -w /opt/app backend …`

Run the full pipeline end-to-end unless the user asks to stop after JSON:

## Stage checklist

```
- [ ] 1 Scrape → collections/<slug>/intermediate/letterboxd_<slug>.json + .meta.json
- [ ] 2 Verify actual_count == expected_count
- [ ] 3 Map KP ids (--slug <key> [--ru-aliases collections/<slug>/intermediate/ru_aliases.json])
- [ ] 4 Resolve TODOs (extend ru_aliases.json; --resume --only-todos)
- [ ] 5 Build collections/<slug>/letterboxd_<slug>_kinopoisk_full.json
- [ ] 6 Promote to backend/src/data/curated/
- [ ] 7 Register LIST_CONFIGS key (e.g. horror_250 → slug letterboxd-horror-250)
- [ ] 8 Prod dry-run seed (--list <key>)
- [ ] 9 Prod apply seed (user confirmed)
- [ ] 10 seed-achievements (+ badges if relevant)
- [ ] 11 cast / director backfills
- [ ] 12 manage_backfill_collection_progress.py (mandatory)
- [ ] 13 Report paths, counts, accepted gaps
```

## Steps (summary)

1. Scrape with `scrape_letterboxd_list.py --slug <key> --url … --expected-count N`
2. Map with `map_lb_kp.py --slug <key>`; tier 3 via `--ru-aliases`; resolve TODOs
3. Build full JSON with `build_lb_kp_full.py --slug <key>` (staff via `GET /v1/staff?filmId=`)
4. Promote + register `LIST_CONFIGS` in `manage_seed_letterboxd_list_full.py`
5. On prod (SSH homelab → service `backend`): dry-run seed → apply (user confirmed) → achievements/badges → cast/director backfills → `manage_backfill_collection_progress.py`
6. Report paths, counts, and any accepted gaps

Ask only for missing blocking inputs (URL, slug key if ambiguous, confirm prod apply).
