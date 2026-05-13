# Progress: abstract-user-cards

## Status
`in_progress`

## Current focus

- **Phase 1 (schema foundation): done.** `CatalogItem`; `movie_card.catalog_item_id` (nullable FK); `film_id` nullable; partial uniques; Kinopoisk `catalog_item` backfill (`u1v2w3x4y890`). **User-owned display fields** on `movie_card`: `display_title`, `display_cover_url`, `display_summary`, `source_url` (all nullable); follow-up migration `w3x4y5z6a012` backfills display fields from linked `film` rows. Model tests under `backend/src/tests/models/test_movie_card_catalog_schema.py`.

## Next steps

- Wire services/API/create flows to prefer `catalog_item_id`; keep joins on `film_id` until clients migrate (both columns remain valid for transitional reads).
- Optional: downgrade smoke on empty DB (`alembic downgrade -1`) if needed for CI.

## Notes

- Source planning reference (read-only): `.cursor/plans/abstract-user-cards-v2_6f1f3132.plan.md` — do not edit that file.
- **Downgrade** fails if `movie_card` rows exist with both `film_id` and resolvable Kinopoisk `catalog_item.film_id` missing (manual / catalog-only drafts); intentional guard in migration.
