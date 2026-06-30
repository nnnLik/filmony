# Monthly Recap and Shareable Summary

## Metadata
- Feature slug: monthly-recap-shareable-summary
- Title: Monthly Recap and Shareable Summary
- Status: planned
- Author: r.makkhmudov
- Created at: 2026-06-30
- Priority: medium
- Target area: fullstack

## Problem
- Users need a lightweight way to revisit their activity and share it.
- A recap can drive retention and create a natural Telegram-sharing moment.

## Scope
- Aggregate a user's monthly activity into a readable summary.
- Add a recap screen and a shareable Telegram-friendly card.

## Functional Requirements
- [ ] Generate a monthly summary from ratings, watchlist changes, comments, and favorites.
- [ ] Render a recap screen with the main stats and top items.
- [ ] Export a compact share card for Telegram sharing.

## Acceptance Criteria
- [ ] The recap is available for the current month and prior months with data.
- [ ] The shareable output works even when the activity volume is low.

## Constraints
- Technical constraints:
- Keep aggregation cheap enough to run on demand or by scheduled job.
- Product/design constraints:
- Do not make the recap feel spammy or overly verbose.

## References
- Related issue/ticket:
- Related files/modules:
