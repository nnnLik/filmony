# Progress Log

## Feature
- Slug: global-feed-sort-by-updated-at
- Status: completed

## Action Entries
### 2026-07-10 23:07
- Action type: plan
- Summary: Opened bugfix workflow for global feed card sorting; documented scope, AC, and implementation plan to switch card `sort_at` from `created_at` to `updated_at`.
- Files:
  - `.cursor/features/global-feed-sort-by-updated-at/feature.md`
  - `.cursor/active/global-feed-sort-by-updated-at/plan.md`
  - `.cursor/active/global-feed-sort-by-updated-at/progress.md`
- Verification:
  - N/A (planning only)
- Notes:
  - Implementation not started; mirrors social feed `updated_at` ordering in `ListGlobalFeedService`.

### 2026-07-10 23:12
- Action type: implementation
- Summary: Switched global feed card branch `sort_at` to `UserCard.updated_at`; posts remain on `FeedPost.created_at`. Updated module/class docstrings.
- Files:
  - `backend/src/services/feed/list_global_feed.py`
- Verification:
  - N/A (tests added next)

### 2026-07-10 23:13
- Action type: test
- Summary: Added API tests for `updated_at` resurfacing (`kind=all`, `kind=cards`); adjusted mixed chronology test to pin card `updated_at` before post `created_at` for deterministic baseline ordering.
- Files:
  - `backend/src/tests/api/test_global_feed_routes.py`
- Verification:
  - `make backend-test-one target=src/tests/api/test_global_feed_routes.py`
  - **9 passed, 0 failed** in 2.42s (Docker `filmony-backend`)
- Notes:
  - Card create flow can bump `updated_at` past subsequent post `created_at`; tests use ORM helper `_card_updated_at_before_post` for stable before/after assertions.

### 2026-07-10 23:20
- Action type: docs
- Summary: Feature closeout complete. Verified planned→rated upgrade (`_finalize_upgraded_planned`) already bumps `updated_at` via `UserCard.updated_at` ORM `onupdate=func.now()` — no service change. Published `result.md` and `docs/features/global-feed-sort-by-updated-at.md`; action-log entry appended.
- Files:
  - `.cursor/active/global-feed-sort-by-updated-at/result.md`
  - `docs/features/global-feed-sort-by-updated-at.md`
  - `.cursor/memory/logs/2026-07-10T201500Z-global-feed-sort-by-updated-at-docs.md`
- Verification:
  - `make backend-test-one target=src/tests/api/test_global_feed_routes.py` — 9 passed (prior run)
  - Planned upgrade path: `backend/src/models/user_card.py` onupdate + `test_movie_card_feed_promotes_converted_planned_card` (social feed, same timestamp semantics)
