# Feature Result

## Feature
- Slug: feed-ordering-updated-at
- Final status: done

## Implemented
- Updated the card feed ordering so user cards sort by `updated_at` instead of `created_at`.
- Covered the planned-card conversion path with a regression test that proves a converted card rises above a newer card in the feed.

## Changed Files
- `backend/src/services/cards/list_user_card_feed.py` - switched card stream ordering to the post-update timestamp.
- `backend/src/tests/api/test_cards_routes.py` - added the regression test for planned-card conversion ordering.
- `.cursor/features/feed-ordering-updated-at/feature.md` - recorded the bugfix scope and acceptance criteria.
- `.cursor/active/feed-ordering-updated-at/plan.md` - captured the implementation plan.
- `.cursor/active/feed-ordering-updated-at/progress.md` - tracked the work log.

## Verification
- Commands/checks executed:
  - `make backend-test-one target=src/tests/api/test_cards_routes.py::test_movie_card_feed_promotes_converted_planned_card`
  - `make backend-test-one target=src/tests/api/test_cards_routes.py`
  - `ReadLints` for the touched backend files
- Results:
  - The focused regression failed before the fix and passed after the feed ordering change.
  - `backend/src/tests/api/test_cards_routes.py` passed with 74 tests in Docker.
  - No linter errors were reported for the touched files.

## Automated tests (backend)
- Updated `backend/src/tests/api/test_cards_routes.py` to cover the feed ordering regression end-to-end through the public API.

## Known Limitations
- The feed still uses the existing merge and anti-spam logic; this fix only changes the timestamp used for card recency ordering.

## Next Steps
- None.
