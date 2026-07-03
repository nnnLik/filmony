# Feed Ordering After Conversion

## Scope
- Fix the card feed so a card upgraded from planned/catalog-later to a normal rated card is ordered by its post-conversion recency.
- Keep existing feed behavior unchanged for non-upgraded cards and for all other card fields.

## Acceptance Criteria
- A card converted from planned to normal appears at the top of the feed when its conversion is the newest card activity.
- Feed ordering remains stable for cards that have not been updated.
- The regression is covered by backend pytest tests in `backend/src/tests/api/test_cards_routes.py`.
