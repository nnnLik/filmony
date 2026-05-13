# Feature Request: Universal User Cards

## Metadata
- Feature slug: `abstract-user-cards`
- Author: (team)
- Created at: 2026-05-13
- Priority: high
- Target area: fullstack

## Problem
- The product is centered on films and Kinopoisk identifiers. Users need a single domain object for “a thing I care about” (film, game, book, manual note, etc.) without Kinopoisk being the conceptual core.
- Production already has 1000+ user cards; any redesign must preserve primary keys, ownership, reactions, feed posts, and statistics.

## Scope
- **In scope:** CardFIRST domain model: `movie_card` → `user_card`, `film` → `catalog_item` with `provider='kinopoisk'` (and provider adapters for external metadata); nullable catalog link on cards; migration that preserves all existing card `id`s and data; phased backend/API/frontend migration with deprecated `film_*` compatibility; Docker-backed backend tests; documentation per project workflow.
- **Out of scope (first delivery):** Adding every external provider at once; making `catalog_item` the user-facing “card”; aggressive removal of all `film`/`movie` naming if it increases migration risk; rewriting watchlist if it stays film-centered; editing `.cursor/plans/abstract-user-cards-v2_6f1f3132.plan.md` (reference copy only).

## Functional Requirements
- [ ] Schema: `user_card` replaces `movie_card` semantics; optional `catalog_item_id`; `catalog_item` dedupes external objects by provider + external id.
- [ ] Migration: row counts and card `id` set unchanged; existing cards backfilled to `catalog_item` where applicable; reactions, feed, comments, mentions, stats still reference the same card ids.
- [ ] Backend: services and reads/writes are card-first; Kinopoisk lives in a provider adapter; community views keyed by `catalog_item_id` where relevant.
- [ ] API: new card/catalog DTOs; transitional deprecated `film_*` fields on responses.
- [ ] Frontend: types and flows for manual cards, catalog-linked cards, and resolver-assisted creation; UI shows user card first, catalog as optional enrichment.
- [ ] Tests: migration invariants, API scenarios, provider resolver; frontend `npm run lint && npm run build`.

## Acceptance Criteria
- [ ] All existing cards remain reachable after migration with the same `id`.
- [ ] Users can create a card with no external source (manual).
- [ ] Users can create a card linked to a `catalog_item`.
- [ ] Kinopoisk is one provider, not the domain anchor.
- [ ] New providers can be added via adapters without sprinkling provider-specific columns on `user_card`.
- [ ] Legacy clients keep working during transition via deprecated compatibility fields.
- [ ] Docker-backed backend tests cover migration and key API paths.
- [ ] `docs/features/abstract-user-cards.md` and `.cursor/active/abstract-user-cards/{plan,progress,result}.md` stay current through delivery.

## Constraints
- **Technical:** Preserve existing card ids and 1000+ rows; conservative migration with verifiable invariants; pytest/ruff in backend container per `.cursor/tech.md`.
- **Product/design:** Universal card UX; external source is optional enhancement (URL/search → resolver → confirm/edit).

## References
- Related issue/ticket: (link if any)
- Related files/modules: `backend/.../models/movie_card.py`, `backend/.../models/film.py`, Alembic migrations, `backend/.../api/cards/`, `backend/.../services/*movie_card*`, `frontend/src/api/*`, card and feed pages/components (see active `plan.md`).
- Planning reference (read-only): `.cursor/plans/abstract-user-cards-v2_6f1f3132.plan.md`
