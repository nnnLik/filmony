# Feed Ordering After Conversion

This bugfix makes upgraded planned cards bubble to the top of the feed immediately after conversion.

## What changed
- The feed now orders user cards by `updated_at` instead of `created_at`.
- A regression test covers the real conversion path from planned card to normal card and checks the upgraded card appears first in the feed.

## Verification
- `make backend-test-one target=src/tests/api/test_cards_routes.py::test_movie_card_feed_promotes_converted_planned_card`
- `make backend-test-one target=src/tests/api/test_cards_routes.py`

## Notes
- The change is intentionally narrow and does not alter non-card feed behavior.
