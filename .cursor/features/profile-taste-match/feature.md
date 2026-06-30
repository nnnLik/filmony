# Taste Match Between Profiles

## Metadata
- Feature slug: profile-taste-match
- Title: Taste Match Between Profiles
- Status: planned
- Author: r.makkhmudov
- Created at: 2026-06-30
- Priority: medium
- Target area: fullstack

## Problem
- Users need a quick way to understand how similar two profiles are.
- This is especially useful for discovery, subscriptions, and public profile browsing.

## Scope
- Compare overlap in genres, ratings, watchlist items, and favorites.
- Show a compact taste-match block in public profile and subscriptions views.

## Functional Requirements
- [ ] API endpoint that compares two profiles and returns a score plus overlap details.
- [ ] UI card that shows the taste match summary and the strongest overlaps.

## Acceptance Criteria
- [ ] The comparison works for profiles with both rich and sparse histories.
- [ ] Empty states explain when there is not enough data to compare meaningfully.

## Constraints
- Technical constraints:
- Keep the calculation deterministic and easy to cache.
- Product/design constraints:
- Do not expose private data beyond what both profiles are allowed to compare.

## References
- Related issue/ticket:
- Related files/modules:
