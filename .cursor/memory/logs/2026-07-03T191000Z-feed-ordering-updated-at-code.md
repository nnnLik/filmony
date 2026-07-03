# Action Log Entry

- Timestamp: 2026-07-03T191000Z
- Feature slug: feed-ordering-updated-at
- Action type: code
- Summary: Added the regression test for planned-card conversion and switched feed card ordering to use `updated_at`.
- Files:
  - `backend/src/tests/api/test_cards_routes.py`
  - `backend/src/services/cards/list_user_card_feed.py`
- Verification:
  - `make backend-test-one target=src/tests/api/test_cards_routes.py::test_movie_card_feed_promotes_converted_planned_card` failed before the fix and passed after the fix.
