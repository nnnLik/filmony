# Implementation Plan: abstract-user-cards

## Feature
- Slug: `abstract-user-cards`
- Source spec: `.cursor/features/abstract-user-cards/feature.md`

## Goal
- Restructure the app around **universal user cards** (`user_card`): `movie_card` becomes `user_card`, `film` is modeled as `catalog_item(provider='kinopoisk')` with provider adapters, optional nullable catalog link on cards, and **no loss** of existing card `id`s, links, reactions, feed posts, or stats (1000+ cards in prod).

## Assumptions
- `catalog_item` is canonical external metadata only; user content and identity stay on `user_card`.
- Transitional period keeps deprecated `film_id` / `film_*` API fields where needed for legacy clients.
- Non-goals for v1: all providers at once; instant purge of every legacy name; watchlist rewrite if still film-scoped.

## Step-by-Step Plan

### Phase 1 — Schema foundation
1. Introduce `catalog_item` and provider model/enum (`kinopoisk` first).
2. Add `user_card` as the renamed/evolved `movie_card` **without changing primary key values** (rename table or equivalent migration path).
3. Add nullable `catalog_item_id` on `user_card`; universal display fields (`title`, `cover_url`, `summary`, optional `source_url`, typed user-layer metadata as designed).
4. Backfill `catalog_item` from existing `film` rows (`provider='kinopoisk'`, `external_id` from current KP id); wire `user_card.catalog_item_id`.
5. Replace `user_id + film_id` uniqueness with partial unique on `(user_id, catalog_item_id)` where `catalog_item_id IS NOT NULL`; allow many manual cards with `NULL` catalog.
6. Add migration tests: row counts, id set equality, backlinks for reactions/feed/comments/mentions/stats.

### Phase 2 — Backend read compatibility
1. Shift read DTOs to `user_card + catalog_item` shape (`card`, `catalog`, `provider`).
2. Keep deprecated `film_*` in responses for transition.
3. Update details/feed/profile/community reads without user-visible behavior regression.

### Phase 3 — Backend write path
1. Manual card creation (no `catalog_item`).
2. Creation by existing `catalog_item_id`.
3. Kinopoisk-first resolver/search → draft normalize → create/find `catalog_item`.
4. Update conflict/uniqueness handling for catalog-linked cards.

### Phase 4 — Frontend migration
1. Rename domain types and API client usage toward card-first naming.
2. Create/edit flows: manual, catalog-linked, resolver-assisted.
3. Detail/feed/profile: render user card first; catalog as badge/source/link; external actions keyed by `provider`.

### Phase 5 — Cleanup
1. Remove or isolate direct `film_id` dependence in card flows when safe.
2. Deprecate or narrow legacy `/api/films/*` as appropriate.
3. Finalize `docs/features/abstract-user-cards.md` and retire redundant compatibility once clients catch up.

## Files Expected To Change
- `backend/src/**/models/movie_card.py`, `backend/src/**/models/film.py`, Alembic under `backend/`, feed/reaction models referencing `MOVIE_CARD`
- `backend/src/**/services/create_movie_card.py`, `update_movie_card.py`, `get_movie_card_details.py`, `list_movie_card_feed.py`, `list_user_movie_cards.py`, `list_film_community_cards.py`, `search_catalog_films.py` (and successors with neutral names)
- `backend/src/**/api/cards/schemas.py`, `backend/src/**/api/cards/routes.py`, `backend/src/**/api/films/routes.py`, catalog routes (`api/catalog/...`)
- `frontend/src/api/profileTypes.ts`, `frontend/src/api/cardApi.ts`, `frontend/src/api/profileApi.ts`, `frontend/src/api/feedInFeedTypes.ts`
- `frontend/src/pages/CreateCardPage*`, `frontend/src/pages/EditMovieCardPage*`, `frontend/src/pages/MovieCardDetailPage*`
- `frontend/src/components/FeedCard*`, `frontend/src/components/FeedPostCard*`
- `backend/src/tests/**` (migration + API + resolver coverage)

## Verification Plan
- **Commands:** `make backend-test` / `make backend-test-one target=…` inside Docker; `cd frontend && npm run lint && npm run build`.
- **Manual checks:** create manual card; create via external source; open pre-migration card; profile and global feed still show historical cards.
- **Backend tests:** migration invariants (counts, id preservation, `catalog_item_id` backfill where expected); manual vs catalog create; duplicate catalog card conflict; multiple NULL-catalog cards; read DTO shape with new fields + deprecated `film_*`; community by `catalog_item_id`; feed/details/profile smoke scenarios; Kinopoisk resolver as first adapter.

## Risks And Mitigations
- **Risk:** Data loss or id churn during migration.
  - **Mitigation:** Conservative Alembic steps, pre/post checks in tests, no row recreation.
- **Risk:** Broken API contract for existing clients.
  - **Mitigation:** Deprecated fields and phased removal; compatibility tests on responses.
- **Risk:** Frontend/API drift during rename.
  - **Mitigation:** Typed DTOs, lint/build gate, slice-by-slice rollout per phase.
