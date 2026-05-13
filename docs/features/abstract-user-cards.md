# Feature: Universal User Cards (`abstract-user-cards`)

## Summary

The product shifts from a **film- and Kinopoisk-centric** card model to **card-first universal user cards**. The persisted row remains `movie_card` with stable ids; optional linkage uses `catalog_item` (provider-discriminated canonical metadata, first provider `kinopoisk`) plus **user-owned display fields** (`display_title`, `display_cover_url`, `display_summary`) so manual cards and transitional reads stay coherent.

## Current implementation (2026-05)

- **Schema:** `catalog_item`; nullable `movie_card.catalog_item_id` and `movie_card.film_id`; partial uniques for duplicates; migrations `u1v2w3x4y890`, `w3x4y5z6a012` (display backfill). Model tests: `backend/src/tests/models/test_movie_card_catalog_schema.py`.
- **Writes:** `POST /api/cards` — film-backed (`film_id` / `kinopoisk_id`, optional `catalog_item_id`), catalog-only (`catalog_item_id`), manual (`display_title` without Kinopoisk/film); validation and 409 on duplicate partial unique.
- **Reads:** Card detail, feed items, profile grids/lists, inline picker, inline card refs, and following-ratings honor nullable film joins and catalog/manual display fields. Deprecated `film_*` populated when a `Film` row exists; otherwise sensible fallbacks (e.g. display title).
- **Resolve:** `POST /api/catalog/resolve` with `{ provider, url }` (Kinopoisk first) upserts `CatalogItem` + nested film payload; `POST /api/films/resolve` unchanged for legacy clients.
- **Frontend:** Types and create wizard (`catalogApi` + legacy film resolve + manual path); `movieCardDisplay` used across detail, feed, profile, share; Kinopoisk UI cues only when `film_kinopoisk_id` is set.

## API and compatibility

New fields: `catalog_item_id`, `display_title`, `display_cover_url`, `display_summary`. Deprecated `film_*` / nullable `film_id` remain for legacy clients until a dedicated cleanup milestone.

## Roadmap / cleanup

- Remove or narrow deprecated `film_*` once all clients consume card-first fields.
- Additional catalog providers beside Kinopoisk.
- Align any remaining statistics DTOs with explicit display metadata if needed.

## Verification

- Backend (Docker): `make backend-test`.
- Frontend: `cd frontend && npm run lint && npm run build`.

## References

- Feature spec: `.cursor/features/abstract-user-cards/feature.md`
- Active delivery notes: `.cursor/active/abstract-user-cards/result.md`
- Read-only planning snapshot: `.cursor/plans/abstract-user-cards-v2_6f1f3132.plan.md`
