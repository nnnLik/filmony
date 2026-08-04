# Global Feed Sort by updated_at Plan

## Feature
- Slug: global-feed-sort-by-updated-at
- Status: in_progress

## Root Cause
- `backend/src/services/feed/list_global_feed.py` — `_union_subquery` card branch sets `UserCard.created_at.label('sort_at')` (line ~74).
- Social feed hydrator path in `list_user_card_feed.py` already orders by `UserCard.updated_at`.

## Plan
1. **Regression test (red)** — extend `backend/src/tests/api/test_global_feed_routes.py`:
   - Create card A (older activity).
   - Create card B and additional feed items so B is not at head.
   - Bump card A’s `updated_at` via a realistic API path (planned metadata edit or planned→rated upgrade).
   - Assert global feed (`kind=cards` and `kind=all`) returns card A before items with older sort timestamps.
2. **Run focused test in Docker** — confirm failure with current `created_at` sorting:
   - `make backend-test-one target=src/tests/api/test_global_feed_routes.py::<new_test_name>`
3. **Service fix** — in `list_global_feed.py`:
   - Change card branch `sort_at` from `UserCard.created_at` to `UserCard.updated_at`.
   - Update module/class docstrings that say «по времени создания» for cards.
   - Cursor encode/decode (`_encode_cursor` / `_decode_cursor`) stays on `sort_at` values — no schema change; cursors naturally carry `updated_at` after fix.
4. **Pagination sanity** — re-run `test_global_feed_pagination_cursor` and mixed chronology test; adjust assertions only if create vs update ordering expectations change.
5. **Verification** — Docker:
   - `make backend-test-one target=src/tests/api/test_global_feed_routes.py`
   - Or full `make backend-test` if quick.
6. **Closeout** — `result.md`, `docs/features/global-feed-sort-by-updated-at.md`, action-log entry.

## Files to Touch (implementation)
- `backend/src/services/feed/list_global_feed.py`
- `backend/src/tests/api/test_global_feed_routes.py`
