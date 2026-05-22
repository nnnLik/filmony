Timestamp: 2026-05-22T153600Z
Feature slug: `rawg-card-linking`
Action type: `code`

## Summary

Remix bootstrap on `CreateCardPage` binds RAWG templates with `catalog_item_id` as `catalog_game` so create payload keeps shared catalog identity.

## Files

- `frontend/src/pages/CreateCardPage.tsx`

## Verification

`cd frontend && npm run lint && npm run build`
