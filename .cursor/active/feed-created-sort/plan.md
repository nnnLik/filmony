# Implementation Plan Template

## Feature
- Slug: `feed-created-sort`
- Source spec: `.cursor/features/feed-created-sort/feature.md`

## Goal
- Desired outcome: Global feed, personal feed, and profile `sort=recent` rank rated cards by **when they became rated** (`UserCard.completed_at`), not by last PATCH (`updated_at`) or insert identity (`id`). Later→rated conversions surface as new; rating/favorite/tags/note edits do not. Indexes and a `rec1.` keyset cursor make the new order paginate safely.

## Assumptions
- `UserCard.completed_at` is already set on new rated create and on later→rated (`CreateUserCardService`); PATCH (`UpdateUserCardService`) does not touch it. This feature only changes **read/sort/index/cursor**, not write paths.
- Later is the same `user_card` row with `is_planned=True`; conversion keeps the same `id` and `created_at`, so profile cannot stay on `id DESC`.
- Historical rated rows already have `completed_at` backfilled (`y3z4a5b6c789`). Feed card branches exclude remaining nulls; profile recent uses `NULLS LAST`.
- Alembic head to revise is `i7j8k9l0m123`. New revision id is `j8k9l0m1n234`.
- `gf1.` global-feed cursor already encodes `sort_at`; switching the card branch label from `updated_at` to `completed_at` is enough (no new cursor prefix).
- Favorites `fav1.{microseconds}.{id}` encoder/decoder is the template for `rec1`.
- `ListUserCardsService.InvalidCursor` is already mapped to HTTP 422 in `api/profile/users_routes.py`.
- Heatmap/streaks/recap keep using `completed_at` as today; no coupling change required if we do not rewrite that column on PATCH.

## Step-by-Step Plan
1. Add Alembic revision `backend/src/migrations/versions/j8k9l0m1n234_user_card_completed_at_feed_indexes.py` with `down_revision = 'i7j8k9l0m123'`. `upgrade` creates `ix_user_card_completed_at_id` on `(completed_at, id)` with `postgresql_ops` DESC/DESC and `postgresql_where` `is_planned IS FALSE AND completed_at IS NOT NULL`; and `ix_user_card_user_id_completed_at_id` on `(user_id, completed_at, id)` DESC/DESC with `WHERE is_planned IS FALSE`. `downgrade` drops both indexes by name.
2. Mirror both indexes on `UserCard.__table_args__` in `backend/src/models/user_card.py` (same names, columns, ops, and `postgresql_where`). Do not add a `published_at` column.
3. In `ListGlobalFeedService` (`backend/src/services/feed/list_global_feed.py`), change the card union branch: `sort_at` = `UserCard.completed_at`; filter `is_planned IS FALSE` and `completed_at IS NOT NULL`. Keep post branch on `FeedPost.created_at`. Keep `ORDER BY sort_at DESC, kind_rank DESC, eid DESC` and the existing `gf1.` cursor. Update the module docstring to completed-at / no PATCH bump.
4. In `ListUserCardFeedService` (`backend/src/services/cards/list_user_card_feed.py`), update `_build_streams._ordered_cards` and `_build_affinity_stream`: exclude planned and null `completed_at`; `ORDER BY UserCard.completed_at.desc(), UserCard.id.desc()`. Affinity Python tie-break uses `-completed_at.timestamp()` (not `-updated_at`). Leave `_build_post_stream` on `FeedPost.created_at`.
5. In `ListUserCardsService._execute_default` for `sort == 'recent'`: `order_by(desc(UserCard.completed_at).nullslast(), desc(UserCard.id))`. Replace numeric `id` cursor with `rec1.{microseconds}.{id}` encode/decode cloned from `_encode_favorites_cursor` / `_decode_favorites_cursor` (`prefix rec1`, unix µs UTC, card id). Keyset: `(completed_at < cursor_dt) OR (completed_at == cursor_dt AND id < cursor_id) OR (completed_at IS NULL)` when the cursor timestamp is non-null. If decode fails (including a bare integer like `"12345"`), raise `InvalidCursor`. Emit `next_cursor` via the new encoder. Do not change `_execute_favorites` (`favorite_marked_at` / `fav1`).
6. Rewrite `test_global_feed_cards_sort_by_updated_at` in `test_global_feed_routes.py`: after PATCH rating on the older card, the **newer-created** card must remain first. Add a sibling test: create later (`POST /api/watchlist` `watch_later`), then `POST /api/cards` to convert, with another rated card created in between; converted card must be first on `GET /api/feed/global?kind=cards`. Also fix `test_global_feed_all_resurfaces_updated_card_above_newer_post` so PATCH rating does **not** lift the card above a newer post (post `created_at` stays ahead of the card’s unchanged `completed_at`).
7. In `test_profile_routes.py`, add coverage: later→rated appears first on `GET /api/users/{id}/cards?sort=recent` despite an older `id`; PATCH rating does not reorder recent; `cursor=12345` returns 422; a `rec1.` `next_cursor` page is stable. Keep favorites tests on `favorite_marked_at`.
8. In `test_movie_card_feed_recommendation.py` (or a new `backend/src/tests/integration/api/test_user_card_feed_created_sort.py` if that module has no convenient hook), assert `GET /api/cards/feed` does not put a PATCHed older card above a newer-created one; later→rated may be asserted there if the slot merge makes the top item observable, otherwise cover conversion on global/profile only and keep personal feed focused on PATCH-does-not-bump.
9. Run the Docker verification commands below; do not treat the feature done if any listed test fails.

## Files Expected To Change
- `backend/src/services/feed/list_global_feed.py`
- `backend/src/services/cards/list_user_card_feed.py`
- `backend/src/services/profile/list_user_cards.py`
- `backend/src/models/user_card.py`
- `backend/src/migrations/versions/j8k9l0m1n234_user_card_completed_at_feed_indexes.py`
- `backend/src/tests/integration/api/test_global_feed_routes.py`
- `backend/src/tests/integration/api/test_profile_routes.py`
- `backend/src/tests/integration/api/test_movie_card_feed_recommendation.py`

## Verification Plan
- Commands to run:
  - `make backend-test-one target=src/tests/integration/api/test_global_feed_routes.py`
  - `make backend-test-one target=src/tests/integration/api/test_profile_routes.py`
  - `make backend-test-one target=src/tests/integration/api/test_movie_card_feed_recommendation.py`
  - If a dedicated personal-feed sort test file is added, run `make backend-test-one target=src/tests/integration/api/test_user_card_feed_created_sort.py` as well.
- Manual checks:
  - Create rated card A, then B; PATCH A rating/favorite/tags/note — B stays on top of global `kind=cards`, personal feed card slots, and profile recent.
  - Add film to later, then rate it after creating another rated card — converted card is first on global cards and profile recent.
  - Planned-only cards never appear in those card streams.
  - Profile recent second page uses `rec1.…`; an old numeric cursor 422s.
  - Favorites tab still orders by favorite mark time.
- **Backend tests:** plan which `backend/src/tests/` modules and cases will cover every new/changed route and service (pytest + pytest-asyncio); implementation is not complete until that full set exists and passes. Runs happen **in Docker** (`make backend-test` / `make backend-test-one target=…`).
  - `backend/src/tests/integration/api/test_global_feed_routes.py`: rewrite `test_global_feed_cards_sort_by_updated_at` (PATCH rating does not win); add later→rated wins on `kind=cards`; adjust `test_global_feed_all_resurfaces_updated_card_above_newer_post` so PATCH does not beat a newer post.
  - `backend/src/tests/integration/api/test_profile_routes.py`: later→rated surfaces on `sort=recent`; PATCH does not reorder; numeric cursor → 422; `rec1` pagination; favorites unchanged (`test_favorites_count_and_favorites_only_list` still valid).
  - `backend/src/tests/integration/api/test_movie_card_feed_recommendation.py` (or new sibling file): personal `GET /api/cards/feed` does not bump on PATCH.

## Risks And Mitigations
- Risk: Clients holding a numeric profile-recent cursor get 422 after deploy.
  - Mitigation: Document the break in feature docs; 422 is already the invalid-cursor contract; clients restart from the first page. Do not silently accept old `id` cursors (wrong order).
- Risk: `completed_at` coupling — a future change to heatmap “completion day” would also move feed/profile recent.
  - Mitigation: Accepted product choice; do not introduce `published_at`. PATCH and heatmap jobs must continue to leave `completed_at` sticky.
- Risk: Partial `completed_at` indexes vs queries that forget `is_planned IS FALSE` / null filters, causing sequential scans or planned leakage.
  - Mitigation: Keep the same predicates in global, personal, and profile queries as in `postgresql_where`; exclude planned/null in feed branches explicitly.
- Risk: Personal feed is slot-merged, so “first item” is not a pure timestamp sort; a naive top-item assert can flake.
  - Mitigation: Prefer comparing relative order of two known card ids in the page (older PATCHed vs newer created), not absolute slot-0; if the recommendation module cannot express that, add a dedicated feed integration test.
- Risk: Alembic head drift if `i7j8k9l0m123` is no longer head at apply time.
  - Mitigation: Confirm `down_revision` against current heads before merge; do not invent a second revision id — keep `j8k9l0m1n234`.
