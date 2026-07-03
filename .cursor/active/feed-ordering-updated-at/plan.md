# Feed Ordering After Conversion Plan

## Feature
- Slug: feed-ordering-updated-at
- Status: in_progress

## Plan
1. Add a regression test that creates a planned card, creates a newer card, converts the planned card, and verifies the converted card moves to the top of the feed.
2. Run the focused backend test to confirm the current feed ordering fails the regression.
3. Update the feed card stream ordering to sort by `updated_at` instead of `created_at` so post-conversion recency is reflected.
4. Re-run the focused regression and nearby backend tests inside Docker.
5. Document the fix in the active result file, feature doc, and action log.
