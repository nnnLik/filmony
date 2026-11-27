# Progress Log: Watch leave Rate create flow

## Feature
- Slug: `watch-leave-rate-create-flow`
- Status: in_progress

## Action Entries
### 2026-08-15 01:35
- Action type: plan
- Summary: Created feature request, implementation plan, and progress log; added slug to HOT in_progress as item 7.
- Files:
  - `.cursor/features/watch-leave-rate-create-flow/feature.md`
  - `.cursor/active/watch-leave-rate-create-flow/plan.md`
  - `.cursor/active/watch-leave-rate-create-flow/progress.md`
  - `.cursor/HOT.md`
- Verification:
  - files exist; status `in_progress`; target frontend; priority high; no TODO placeholders
- Notes:
  - Implementation not started. Next: branch Rate destination in `watchLeaveRatePrompt.ts` and wire `FilmWatchPage` / `FilmDetailPage`.

### 2026-08-15 01:40
- Action type: code/test
- Summary: Added `filmRateCardPath(opts)` for Rate destinations; wired FilmWatchPage (Rate after watch) and FilmDetailPage (add CTA / hasMyRatedCard).
- Files:
  - `frontend/src/lib/watchLeaveRatePrompt.ts`
  - `frontend/src/lib/__tests__/watchLeaveRatePrompt.test.ts`
  - `frontend/src/pages/FilmWatchPage.tsx`
  - `frontend/src/pages/FilmDetailPage.tsx`
- Verification:
  - `cd frontend && npx vitest run src/lib/__tests__/watchLeaveRatePrompt.test.ts` — 5 passed
  - eslint on the four files above — passed
- Notes:
  - `filmRateCardPath`: rated → `/cards/{id}/edit`; planned → `/cards/new?fromCard=&intent=rate`; none → `/cards/new?filmId=`
  - FilmWatchPage Rate after watch uses `my_card_id` + planned card (prefetch + await if query not success)
  - FilmDetailPage `hasMyRatedCard` excludes planned; add CTA uses `filmRateCardPath`
  - Status remains `in_progress` (docs / `result.md` not published yet)
