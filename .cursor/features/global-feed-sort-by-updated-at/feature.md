# Global Feed Sort by updated_at

## Scope
- Fix global feed (`/api/feed/global`) so **movie cards** are ordered by `UserCard.updated_at`, not `created_at`.
- Align global feed card ordering with the social/subscribed feed, which already uses `updated_at`.
- Posts in global feed keep `FeedPost.created_at` as sort key (unchanged).

## Problem
- A card created as «позже»/planned appears at the top on create (newest `created_at`).
- After more feed activity, updating or upgrading that card bumps `updated_at` but the card stays lower in the feed because `ListGlobalFeedService` sorts cards by `created_at`.
- Users expect resurfacing at the top when card activity is newer than surrounding items.

## Acceptance Criteria
- After a planned card’s `updated_at` is bumped (metadata edit, deferred-film view sync, or upgrade to rated), it appears **above** older global-feed items whose sort timestamps are older.
- Mixed `kind=all` feed still orders cards vs posts by each branch’s `sort_at` (cards: `updated_at`; posts: `created_at`).
- Keyset pagination (`next_cursor` / `cursor`) remains correct for cards-only, posts-only, and mixed feeds.
- Regression covered by pytest in `backend/src/tests/api/test_global_feed_routes.py`.
- Existing global-feed tests that assert create-time chronology still pass where `created_at` equals `updated_at` on first create.

## Out of Scope
- Social/subscribed feed ordering (already correct).
- Changing post sort field.
- Frontend changes.
