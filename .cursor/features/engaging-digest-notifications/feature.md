# Engaging Digest Notifications

## Metadata
- Feature slug: `engaging-digest-notifications`
- Title: Richer Subscribed-Activity Digest Copy
- Status: done
- Target area: backend / telegram

## Problem Statement
The 48-hour subscribed-activity Telegram digest uses a dull fixed template: generic header plus three plain numbered lines. Users miss genre context, rating highlights, activity counts, and window-level trends that already exist in the data model.

## Goals
- Redesign digest message assembly with varied intros driven by real window stats (genres, avg rating, event counts, favorites).
- Enrich per-item copy with genres, year, rating, tags, mood-after, and author activity breakdowns.
- Keep 48h cadence, selection logic, and idempotency unchanged.
- Graceful fallbacks when data is sparse.

## Non-Goals
- Changing Celery schedule or digest interval.
- New API endpoints or user settings.
- Leaking private stats of users the recipient does not follow.

## Acceptance Criteria
- Digest HTML is built by a dedicated message builder service.
- Window stats (genres, ratings, counts) appear in intro when data supports it.
- Item lines use kind-specific rich templates with fallbacks for missing fields.
- pytest covers message builder and existing digest delivery tests still pass.
