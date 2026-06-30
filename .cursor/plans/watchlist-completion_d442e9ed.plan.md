---
name: watchlist-completion
overview: "Finish the unified watchlist feature end-to-end: mutual watch-with selection, provider-aware tags and create flows, rich watchlist feed posts, and the remaining frontend UX for profile/watchlist management."
todos:
  - id: backend-watchwith
    content: Finish backend watch-with validation, tag plumbing, and provider-aware shims
    status: completed
  - id: backend-feed
    content: Replace placeholder watchlist feed posts with real snapshot content
    status: completed
  - id: frontend-create
    content: Add watch-with picker, tag selector, and provider-aware watchlist create UI
    status: completed
  - id: legacy-cleanup
    content: Remove or deprecate legacy watchlist film-only endpoints and finish migration cleanup
    status: in_progress
  - id: delivery-artifacts
    content: Update progress, result, docs, and action log; run final verification
    status: pending
isProject: false
---

# Watchlist Feature Completion Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete the watchlist feature so users can add Kinopoisk, RAWG, and custom cards to one unified "Позже" list, choose a mutual friend and tag when creating a watchlist entry, and see the result reflected in profile, feed, and invite flows.

**Architecture:** Keep the unified `WatchlistEntry` model and list/create API, but finish the product flows around it: mutual friend selection is computed from the intersection of `followers` and `following`, `watch_tag` and `watch_with_user_id` are first-class fields in the create payload, and watchlist feed posts should render a real card snapshot instead of a placeholder body. Frontend should drive all providers through one create path and one profile watchlist list, with provider-aware navigation and entry actions.

**Tech Stack:** FastAPI, SQLAlchemy/Alembic, React, Telegram push, pytest/pytest-asyncio, frontend vitest, Docker-backed backend test commands.

---

## Flow Overview

```mermaid
flowchart LR
  CreateCardPage[CreateCardPage] --> PayloadBuilder[WatchlistPayloadBuilder]
  PayloadBuilder --> MeRoutes[POST /api/me/watchlist]
  MeRoutes --> CreateWatchlistEntryService[CreateWatchlistEntryService]
  CreateWatchlistEntryService --> FeedPostService[CreateWatchlistFeedPostService]
  CreateWatchlistEntryService --> InviteNotificationService[SendWatchlistInviteNotificationService]
  CreateWatchlistEntryService --> WatchlistListAPI[GET /api/users/{user_id}/watchlist]
  WatchlistListAPI --> ProfileWatchlistTab[Profile "Позже" tab]
```

---

## Task 1: Finish backend watch-with and tag plumbing

**Files:**
- Modify: `backend/src/services/watchlist/create_watchlist_entry.py`
- Modify: `backend/src/services/watchlist/create_watchlist_entry_from_film.py`
- Modify: `backend/src/services/watchlist/create_watchlist_entry_from_catalog.py`
- Modify: `backend/src/api/profile/me_routes.py`
- Modify: `backend/src/api/watchlist/schemas.py`
- Modify: `backend/src/api/profile/schemas.py`
- Test: `backend/src/tests/services/test_create_watchlist_entry_service.py`
- Test: `backend/src/tests/api/test_watchlist_routes.py`

- [ ] **Step 1: Write the failing tests first**
  - Mutual-watch validation rejects a non-mutual `watch_with_user_id`.
  - `film_id` and `catalog_item_id` shims forward `watch_with_user_id` and `watch_tag` instead of forcing `None`.
  - The create route accepts the typed `watch_tag` payload on every path.

- [ ] **Step 2: Implement the minimal backend changes**
  - Validate that the invited user exists and is part of the mutual subscriptions intersection before creating the second entry.
  - Forward `watch_with_user_id` and `watch_tag` through the film/catalog shims.
  - Keep the current unified create path for custom cards.

- [ ] **Step 3: Verify the backend behavior**
  - Run the new watch-with and shim tests in Docker.
  - Confirm the route still returns the created entry shape for Kinopoisk, RAWG, and custom payloads.

---

## Task 2: Replace the placeholder watchlist feed post with a real snapshot

**Files:**
- Modify: `backend/src/services/feed_posts/create_watchlist_feed_post.py`
- Modify: `backend/src/services/watchlist/list_user_watchlist_entries.py` if it needs extra hydrated fields for feed rendering
- Modify: `backend/src/api/profile/schemas.py` and/or `backend/src/api/feed/schemas.py` if the watchlist feed item shape changes
- Test: `backend/src/tests/services/test_create_watchlist_feed_post_service.py`
- Test: `backend/src/tests/api/test_feed_routes.py` or the existing feed API test file that renders feed cards

- [ ] **Step 1: Write the failing test**
  - Assert the feed post payload includes a real watchlist snapshot: title, description, poster image, comments/emotions scope, and no personal rating.

- [ ] **Step 2: Implement the feed snapshot**
  - Use the provider metadata and hydrated card data to build the feed post body.
  - Keep the post generic enough to support Kinopoisk, RAWG, and custom cards.
  - Preserve the requirement that a feed post is created on every watchlist add.

- [ ] **Step 3: Verify feed rendering**
  - Run the feed service/API tests and make sure the feed can still list rated cards and the new watchlist post type.

---

## Task 3: Finish the frontend watch-with, tag, and provider-aware create flow

**Files:**
- Modify: `frontend/src/pages/CreateCardPage.tsx`
- Modify: `frontend/src/components/share/ShareFollowersPicker.tsx` or create a dedicated mutual-friend picker component
- Modify: `frontend/src/api/profileApi.ts`
- Modify: `frontend/src/api/profileTypes.ts`
- Modify: `frontend/src/pages/FilmDetailPage.tsx`
- Modify: `frontend/src/pages/ProfilePage.tsx`
- Modify: `frontend/src/pages/PublicProfilePage.tsx`
- Modify: `frontend/src/components/profile/WatchlistPosterGrid.tsx`
- Modify: `frontend/src/navigation/TelegramMiniAppStartParamRedirect.tsx`
- Modify: `frontend/src/lib/miniAppCardDeepLink.ts`
- Test: `frontend/src/api/profileApi.test.ts`
- Test: component/page tests for `CreateCardPage` and `WatchlistPosterGrid` if the repo already uses them for these screens

- [ ] **Step 1: Write the failing UI/API tests**
  - `postCreateWatchlistEntry` sends `watch_tag` and `watch_with_user_id`.
  - The create page shows a watch-with picker built from the mutual subscriptions intersection (`followers` ∩ `following`).
  - The profile grid shows a created watchlist item and provider-aware navigation for Kinopoisk, RAWG, and custom entries.

- [ ] **Step 2: Implement the UI flow**
  - Add a watch-with picker and a `watch_tag` selector to the CreateCardPage watchlist step.
  - Use the universal create payload for all providers so RAWG and custom cards can also be added to watchlist with the same form.
  - Update profile watchlist rendering/actions so own entries can be deleted or edited from the list.
  - Add invite deeplink handling so the Telegram link lands in the correct watchlist flow.

- [ ] **Step 3: Verify frontend behavior**
  - Run the API tests, lint, and build.
  - Confirm the profile list refreshes after create/delete and the item appears immediately.

---

## Task 4: Close the legacy cleanup and tighten backend routes

**Files:**
- Modify: `backend/src/api/profile/me_routes.py`
- Modify: `backend/src/api/watchlist/routes.py`
- Modify: `backend/src/migrations/versions/w1x2y3z4a02_migrate_watchlist_films.py` or add a drop-legacy migration
- Modify: `backend/src/tests/migrations/test_watchlist_migration.py`
- Modify: `backend/src/tests/api/test_watchlist_routes.py`

- [ ] **Step 1: Decide and encode the cleanup boundary**
  - Remove or fully deprecate the legacy film-only endpoints once the frontend no longer depends on them.
  - Add the missing migration step that drops the legacy `user_watchlist_film` table after data is migrated.

- [ ] **Step 2: Implement and test the cleanup**
  - Keep the compatibility path only if the plan explicitly needs it; otherwise route everything through the universal watchlist API.
  - Add a migration test for the legacy-table removal or the final migration sequence.

- [ ] **Step 3: Verify the final API surface**
  - Confirm all new watchlist routes, create flows, and cleanup migrations pass in Docker.

---

## Task 5: Delivery artifacts and final verification

**Files:**
- Modify: `.cursor/active/watchlist-cards/progress.md`
- Create/Modify: `.cursor/active/watchlist-cards/result.md`
- Create/Modify: `docs/features/watchlist-cards.md`
- Modify: `.cursor/memory/logs/action-log.md` and the matching fragment for this date/feature

- [ ] **Step 1: Record progress as the work lands**
  - Update progress after each meaningful backend or frontend milestone.

- [ ] **Step 2: Publish the result docs**
  - Summarize what shipped, what remains, and the exact verification commands/results.

- [ ] **Step 3: Final verification before completion**
  - Backend: run the relevant Docker pytest commands for the changed watchlist, feed, and migration tests.
  - Frontend: run `cd frontend && npm test -- src/api/profileApi.test.ts && npm run lint && npm run build`.

---

## Acceptance Checklist
- Unified watchlist accepts Kinopoisk, RAWG, and custom cards from the same create flow.
- The user can choose a mutual friend for watch-with and the invited user gets a separate entry plus Telegram notification.
- The watchlist list is visible in profile immediately after create.
- `watch_tag` is wired through the UI and backend, even if v1 only exposes the current enum value.
- Watchlist feed posts are no longer placeholder text.
- Legacy film-only flow is removed or explicitly deprecated after migration.
