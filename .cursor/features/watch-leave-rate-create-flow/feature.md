# Feature Request: Watch leave Rate create flow

## Metadata
- Feature slug: `watch-leave-rate-create-flow`
- Title: Route Rate/Оценка from watch leave to create when the card is planned
- Status: in_progress
- Author: cursor-agent
- Created at: 2026-08-15T013500Z
- Priority: high
- Target area: frontend

## Problem
- After watching a film, tapping Rate/Оценка uses `filmRateCardPath(filmId, my_card_id)` → `/cards/{id}/edit` whenever `my_card_id` exists.
- `my_card_id` is also set for planned («Позже») cards, so users land on edit, which redirects to edit-planned, instead of the existing later→rated create flow: `/cards/new?fromCard={id}&intent=rate` (same rule as `plannedCardRateHref` on `MovieCardDetailPage`).
- This is important now because the watch-leave CTA currently blocks rating a film that is only on the later list.

## Scope
- In scope:
  - Change the Rate/Оценка destination so edit is used only when the viewer already has a **rated** card (not `is_planned`).
  - If a planned card exists → `/cards/new?fromCard={id}&intent=rate`.
  - If no card → `/cards/new?filmId=`.
  - Apply the same CTA rule on watch leave (`FilmWatchPage`) and film detail (`FilmDetailPage`).
  - Update `watchLeaveRatePrompt.ts` and its unit test.
- Out of scope:
  - Backend card APIs, planned-card edit screens, and new create-flow UI.
  - Changing `MovieCardDetailPage` planned-rate href (reference behavior only).

## Functional Requirements
- [ ] Rate/Оценка navigates to `/cards/{id}/edit` only when the viewer already has a rated card (`my_card_id` present and not planned).
- [ ] Rate/Оценка navigates to `/cards/new?fromCard={id}&intent=rate` when the viewer has a planned card.
- [ ] Rate/Оценка navigates to `/cards/new?filmId=` when the viewer has no card.
- [ ] `FilmWatchPage` and `FilmDetailPage` share this CTA rule.

## Acceptance Criteria
- [ ] Planned-card viewers never open edit (or edit-planned) from Rate/Оценка on watch leave or film detail.
- [ ] Rated-card viewers still open `/cards/{id}/edit`.
- [ ] Viewers with no card still open `/cards/new?filmId=`.
- [ ] Unit tests for `watchLeaveRatePrompt` cover rated / planned / no-card destinations.
- [ ] Frontend lint and build pass for touched files.

## Constraints
- Technical constraints:
  - Frontend only.
  - Reuse the existing later→rated create query (`fromCard` + `intent=rate`); do not invent a new route.
- Product/design constraints:
  - Copy and CTA labels stay Rate/Оценка; only the destination changes.

## References
- Related issue/ticket: none
- Related files/modules:
  - `frontend/src/lib/watchLeaveRatePrompt.ts`
  - `frontend/src/lib/__tests__/watchLeaveRatePrompt.test.ts`
  - `frontend/src/pages/FilmWatchPage.tsx`
  - `frontend/src/pages/FilmDetailPage.tsx`
  - `frontend/src/pages/MovieCardDetailPage.tsx` (`plannedCardRateHref` — reference)
