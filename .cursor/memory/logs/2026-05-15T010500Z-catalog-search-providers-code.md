# Action log fragment

## Timestamp

2026-05-15T01:05:00Z

## Feature slug

catalog-search-providers

## Action type

code

## Summary

Frontend create-card wizard: step 1 is search-first with type picker (Kinopoisk / RAWG / manual). Added `searchCatalog()` and DTO types; game cards submit via `catalog_item_id` with display fields.

## Files

- `frontend/src/api/catalogApi.ts`
- `frontend/src/api/cardApi.ts`
- `frontend/src/api/profileTypes.ts`
- `frontend/src/pages/CreateCardPage.tsx`
- `frontend/src/lib/openExternalUrl.ts`
- `.cursor/active/catalog-search-providers/progress.md`

## Verification

`cd frontend && npm run lint && npm run build` — passed.
