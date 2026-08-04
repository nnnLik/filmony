# Product Ideas Research — Plan

## Goal
Curate 10–20 ranked feature ideas grounded in Filmony's shipped domains, not generic social-app suggestions.

## Method
1. Inventory **shipped** capabilities via `docs/features/` (51 outcome docs) and `.cursor/features/index.yaml`.
2. Map **product surfaces**: `frontend/src/routes.tsx` (feed, search, cards, watchlist, profiles, films, feed-posts).
3. Map **backend domains**: cards, feed, feed_posts, watchlist, subscriptions, catalog (Kinopoisk + RAWG), reactions, telegram, profile stats, search.
4. Exclude fully shipped features and note already-planned specs (`.cursor/features/*`) without re-listing them as "new."
5. Rank by **user value × fit with existing infra × incremental effort**.

## Outputs
- `.cursor/active/product-ideas-2026-07/result.md` — ranked backlog with S/M/L and dependencies.
- `docs/features/product-ideas-backlog.md` — stable index for product discussions.

## Exclusions (already shipped or in active specs)
- Subscriptions graph, feed recommendation engine, watchlist cards, abstract user cards, custom reactions, profile analytics v1, CSV export, Telegram digests, global feed tabs/SSE (in progress).
- Planned specs referenced but not duplicated: `profile-taste-match`, `monthly-recap-shareable-summary`, `youtube-card-source`, `feed-explainability-export-offline`, doppelganger layer (008).
