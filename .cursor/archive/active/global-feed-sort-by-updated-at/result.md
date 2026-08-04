# Feature Result

## Feature
- Slug: global-feed-sort-by-updated-at
- Final status: done

## Implemented
- Switched global feed card branch `sort_at` from `UserCard.created_at` to `UserCard.updated_at` in `ListGlobalFeedService`.
- Posts in global feed still sort by `FeedPost.created_at` (unchanged).
- Added API regression tests for `kind=cards` and `kind=all` resurfacing when a card’s `updated_at` is bumped via PATCH.
- Adjusted mixed chronology baseline test to pin card `updated_at` before post `created_at` for deterministic ordering.

## Changed Files
- `backend/src/services/feed/list_global_feed.py` — card union branch uses `UserCard.updated_at` as `sort_at`; docstrings updated.
- `backend/src/tests/api/test_global_feed_routes.py` — `test_global_feed_cards_sort_by_updated_at`, `test_global_feed_all_resurfaces_updated_card_above_newer_post`; `_card_updated_at_before_post` helper; mixed chronology baseline fix.

## Verification
- Commands/checks executed:
  - `make backend-test-one target=src/tests/api/test_global_feed_routes.py`
- Results:
  - **9 passed, 0 failed** in Docker (`filmony-backend`).

## Planned → rated upgrade and `updated_at`
- **Already bumps `updated_at` — no code change required.**
- `CreateUserCardService._finalize_upgraded_planned` mutates the planned `UserCard` row and commits; `UserCard.updated_at` has `onupdate=func.now()` on the ORM column (`backend/src/models/user_card.py`), so the upgrade issues an UPDATE and refreshes the timestamp.
- Cross-feature evidence: social/subscribed feed regression `test_movie_card_feed_promotes_converted_planned_card` in `backend/src/tests/api/test_cards_routes.py` (feature `feed-ordering-updated-at`) already proves planned→rated conversion promotes the card when ordering by `updated_at`.

## Automated tests (backend)
- `backend/src/tests/api/test_global_feed_routes.py` — full global-feed surface for this fix (9 tests).

## Known Limitations
- Opening a card detail view (GET) alone does **not** bump `updated_at`; only mutating flows (edit, planned upgrade, deferred-film view sync, etc.) do.
- Posts in global feed still sort by `created_at`, not `updated_at`.
- Keyset cursors issued before a card update may be slightly inconsistent if that card is updated mid-pagination (inherent to `updated_at` ordering; same as social feed).

## Next Steps
- None.
