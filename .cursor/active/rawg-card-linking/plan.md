# RAWG card linking (fromCard / friends ratings)

## Problem

`/cards/new?fromCard=…` cloned non-film cards as manual, dropping `catalog_item_id`. RAWG-backed cards therefore lost shared catalog identity; `following-ratings` could not align peers by `catalog_item_id`.

## Plan

1. **Frontend:** In `CreateCardPage.tsx`, after loading the template card, if `film_id` is absent but `provider === 'rawg'` and `catalog_item_id` is set, bind `creationBinding` as `catalog_game` (reuse display fields + `movieCardReleaseCompactSuffix` for subtitle). Keep existing film bootstrap and generic manual fallback.
2. **Backend:** Prove service behavior with API tests — same `catalog_item_id`, subscribed viewer sees followed users’ ratings; include `viewer_rating` parity with film flow.
3. **Docs:** Update `docs/features/movie-card-following-ratings.md` (matching rules, service filename, remix note).
4. **Memory:** Append action-log entries.

## Acceptance

- Remix from RAWG catalog card submits with `catalog_item_id` via catalog-game payload.
- New pytest coverage for RAWG shared catalog + subscriptions.
- Frontend lint/build and backend targeted pytest pass.
