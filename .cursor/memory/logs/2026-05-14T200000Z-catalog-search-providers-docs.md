# Action log fragment

## Timestamp

2026-05-14T200000Z

## Feature slug

catalog-search-providers

## Action type

docs

## Summary

Added **v2 API / legacy naming cleanup roadmap** for retiring `movie_card*` wire, Celery task names, and (late phase) DB table names while keeping `film_*` domain fields where they denote the Film entity. Linked the map from feature docs and active `result.md`; updated action-log index.

## Files

- `docs/features/catalog-search-providers-compat-cleanup-map.md` (new)
- `docs/features/catalog-search-providers.md`
- `.cursor/active/catalog-search-providers/result.md`
- `.cursor/memory/logs/action-log.md`
- `.cursor/memory/logs/2026-05-14T200000Z-catalog-search-providers-docs.md`

## Verification

- Planning/documentation only; **no runtime code changes**.
- Review: map covers Phase 0–5, additive vs breaking steps, reaction `target_kind`, Celery, frontend lockstep, DB rename risk, rollback notes.

## Links

- Map: `docs/features/catalog-search-providers-compat-cleanup-map.md`
