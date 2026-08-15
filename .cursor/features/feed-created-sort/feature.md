# Feature Request Template

## Metadata
- Feature slug: `feed-created-sort`
- Title: Sort feed and profile recent by rated-card creation (`completed_at`)
- Status: in_progress
- Author: r.makkhmudov
- Created at: 2026-08-15
- Priority: high
- Target area: backend

## Problem
- What user/problem are we solving?
  Global feed (`GET /api/feed/global`), personal feed (`GET /api/cards/feed`), and profile recent (`GET /api/users/{id}/cards?sort=recent`) currently surface last-**updated** (or last-inserted `id`) rated cards. A rating change, favorite toggle, tags, or note bump can send an old card to the top. Product wants last-**created** rated cards: (1) a new rated `UserCard` from scratch, or (2) converting an `is_planned` later card into a rated card. Edits after that moment must not reshuffle the stream.
- Why is this important now?
  The current `updated_at` / `id DESC` contracts make the feed feel noisy and unfair: editing a rating looks like a new review. Later→rated keeps the same primary key, so profile recent (`id DESC`) never shows conversions as new. Shipping the sort on existing `UserCard.completed_at` (already set on create and later→rated, never on PATCH) unblocks the product rule without a new timestamp column.

## Scope
- In scope:
  - Global feed card branch: sort by `UserCard.completed_at DESC, id DESC`; exclude `is_planned` and `completed_at IS NULL`. Posts stay on `FeedPost.created_at`.
  - Personal feed card streams (including affinity tie-break): same `completed_at DESC, id DESC` and planned/null exclusion. Posts stay on `FeedPost.created_at`.
  - Profile `sort=recent`: `completed_at DESC NULLS LAST, id DESC` (not `id DESC`). Favorites tab stays `favorite_marked_at`.
  - Profile recent cursor: `rec1.{microseconds}.{id}` (same shape as `fav1` favorites cursor). Legacy numeric `id` cursor → `InvalidCursor` (HTTP 422).
  - Indexes `ix_user_card_completed_at_id` and `ix_user_card_user_id_completed_at_id` via Alembic revision `j8k9l0m1n234` (`down_revision = i7j8k9l0m123`), mirrored on `UserCard.__table_args__`.
  - Integration tests for PATCH-does-not-win, later→rated-does-win (global + profile), and personal feed PATCH-does-not-bump.
- Out of scope:
  - New `published_at` / `rated_at` column.
  - Changing when `completed_at` is written (create + later→rated already correct; PATCH must stay a no-op).
  - Heatmap, streaks, recap, gamification, collections `completed_at` semantics.
  - Favorites tab order, rating_desc / rating_asc sorts, watchlist UI.
  - Frontend changes.
  - Rewriting `created_at` on later→rated.

## Functional Requirements
- [ ] Rated-card “creation” for sort is `UserCard.completed_at`: new rated insert **or** later→rated conversion (`is_planned` False + `completed_at` set).
- [ ] `PATCH /api/cards/{id}` for rating, favorite, tags, or note must not change `completed_at` and must not move the card to the top of global feed, personal feed, or profile `sort=recent`.
- [ ] `GET /api/feed/global` card stream orders by `completed_at DESC, id DESC` and omits planned / null-`completed_at` cards; `kind=all` still merges posts by `FeedPost.created_at` (existing `gf1.` cursor encodes that `sort_at`).
- [ ] `GET /api/cards/feed` card streams (subscriptions, subscribers, discovery, own, affinity) order by `completed_at DESC, id DESC` and omit planned / null-`completed_at`; post stream unchanged.
- [ ] `GET /api/users/{id}/cards` with `sort=recent` (not favorites) orders by `completed_at DESC NULLS LAST, id DESC`. Later→rated surfaces at the top despite a stable `id`.
- [ ] Profile recent pagination cursor is `rec1.{unix_microseconds}.{id}`. A bare numeric `id` cursor is rejected as `ListUserCardsService.InvalidCursor`.
- [ ] Favorites + `sort=recent` remains `favorite_marked_at DESC, id DESC` with `fav1.` cursor.
- [ ] Alembic `j8k9l0m1n234` adds the two `completed_at` indexes; SQLAlchemy model indexes match.

## Acceptance Criteria
- [ ] After two rated cards, a PATCH rating on the older card does **not** make it first on `GET /api/feed/global?kind=cards`.
- [ ] Converting a later card to rated **does** place that card first on global `kind=cards` and on profile `sort=recent`, even when a newer-id rated card exists.
- [ ] Personal `GET /api/cards/feed` does not promote a card after PATCH rating / favorite.
- [ ] Planned cards do not appear in global or personal card streams.
- [ ] Profile `sort=recent` with cursor `12345` (numeric) returns 422 invalid cursor; a `rec1.` cursor from a previous page continues correctly.
- [ ] Favorites tab order is unchanged.
- [ ] `make backend-test-one` for the listed integration tests passes inside Docker.

## Constraints
- Technical constraints:
  - Reuse `UserCard.completed_at` only. Do not add `published_at`.
  - Alembic: `revision = j8k9l0m1n234`, `down_revision = i7j8k9l0m123`.
  - Index names: `ix_user_card_completed_at_id` (`completed_at`, `id`) and `ix_user_card_user_id_completed_at_id` (`user_id`, `completed_at`, `id`), DESC ops; partial `WHERE is_planned IS FALSE` (and `completed_at IS NOT NULL` on the global/feed index).
  - Service layer owns query/sort/cursor; routes stay thin. No business logic in DAOs beyond persistence.
  - Tests live under `backend/src/tests/integration/` (HTTP/DB). Run via Docker (`make backend-test-one`).
- Product/design constraints:
  - Creation = new rated card **or** later→rated. Rating/favorite/tags/note must not bump.
  - Profile recent must surface later→rated; `id DESC` is insufficient because conversion keeps the same PK.
  - Breaking change: old numeric recent cursors become invalid (clients must restart pagination).

## References
- Related issue/ticket: none
- Related files/modules:
  - `backend/src/services/feed/list_global_feed.py`
  - `backend/src/services/cards/list_user_card_feed.py`
  - `backend/src/services/profile/list_user_cards.py`
  - `backend/src/models/user_card.py`
  - `backend/src/migrations/versions/j8k9l0m1n234_user_card_completed_at_feed_indexes.py`
  - `backend/src/tests/integration/api/test_global_feed_routes.py`
  - `backend/src/tests/integration/api/test_profile_routes.py`
  - `backend/src/tests/integration/api/test_movie_card_feed_recommendation.py`
  - `backend/src/services/cards/create_user_card.py` (already sets `completed_at`; read-only for this feature)
  - `backend/src/services/cards/update_user_card.py` (must keep PATCH off `completed_at`)
  - `backend/src/api/profile/users_routes.py` (`InvalidCursor` → 422)
