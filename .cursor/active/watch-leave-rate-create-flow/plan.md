# Implementation Plan: Watch leave Rate create flow

## Feature
- Slug: `watch-leave-rate-create-flow`
- Source spec: `.cursor/features/watch-leave-rate-create-flow/feature.md`

## Goal
- Desired outcome: Rate/Оценка after watch (and the matching film-detail CTA) opens edit only for an existing rated card; planned cards use `/cards/new?fromCard={id}&intent=rate`; no card uses `/cards/new?filmId=`.

## Assumptions
- `my_card_id` is present for both rated and planned viewer cards; planned vs rated is distinguishable via `is_planned` (or equivalent) on the film/watch payload already used by these pages.
- `MovieCardDetailPage` `plannedCardRateHref` is the correct later→rated create contract to reuse, not to change.
- `filmRateCardPath(filmId, my_card_id)` currently always maps a present `my_card_id` to `/cards/{id}/edit`; that helper (or its callers) must branch on planned vs rated.

## Step-by-Step Plan
1. Extend `watchLeaveRatePrompt.ts` so the Rate path is:
   - rated card (`my_card_id` and not planned) → `/cards/{id}/edit`
   - planned card → `/cards/new?fromCard={id}&intent=rate`
   - no card → `/cards/new?filmId=`
2. Align `FilmWatchPage.tsx` and `FilmDetailPage.tsx` Rate/Оценка CTAs with that helper so both screens use the same rule.
3. Update `frontend/src/lib/__tests__/watchLeaveRatePrompt.test.ts` for rated, planned, and no-card destinations (and any regression that previously treated any `my_card_id` as edit).
4. Run frontend lint and build on touched files.

## Files Expected To Change
- `frontend/src/lib/watchLeaveRatePrompt.ts`
- `frontend/src/lib/__tests__/watchLeaveRatePrompt.test.ts`
- `frontend/src/pages/FilmWatchPage.tsx`
- `frontend/src/pages/FilmDetailPage.tsx`

## Verification Plan
- Commands to run:
  - `cd frontend && npm run lint && npm run build`
  - targeted unit test for `frontend/src/lib/__tests__/watchLeaveRatePrompt.test.ts`
- Manual checks:
  - Watch leave Rate with a planned card → create `fromCard` + `intent=rate`, not edit-planned.
  - Watch leave Rate with a rated card → `/cards/{id}/edit`.
  - Watch leave Rate with no card → `/cards/new?filmId=`.
  - Film detail Rate/Оценка matches the same three destinations.
- **Backend tests:** not applicable (frontend only).

## Risks And Mitigations
- Risk: Film detail uses a different path helper than watch leave, so only one screen gets the fix.
  - Mitigation: Apply the same CTA rule in both `FilmWatchPage.tsx` and `FilmDetailPage.tsx`; keep routing logic in `watchLeaveRatePrompt.ts` (or a shared helper it already owns).
- Risk: Planned flag missing or named differently on one payload, so planned cards still hit edit.
  - Mitigation: Match the field already used for planned vs rated on these pages; cover planned vs rated in unit tests.
