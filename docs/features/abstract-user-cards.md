# Feature: Universal User Cards (`abstract-user-cards`)

## Summary
The product moves from a **film- and Kinopoisk-centric** model to **card-first universal user cards**. A user’s primary object is a `user_card` (evolution of today’s `movie_card`). Optional external metadata is attached via `catalog_item` (evolution of today’s `film` rows) with a `provider` such as `kinopoisk`, with room for future providers without polluting `user_card` with provider-specific columns.

## Domain model (target)
- **`user_card`:** User-owned record: content, visibility, reactions, feed posts, statistics. Same primary keys as today’s cards **must** be preserved (1000+ cards in production).
- **`catalog_item`:** Optional canonical external object (deduped by provider + external id). Not a substitute for a user card.
- **Providers / adapters:** Resolve URLs or search, normalize metadata (first implementation: Kinopoisk).

## Migration mapping
```text
movie_card → user_card
film       → catalog_item(provider='kinopoisk')
```

Nullable `catalog_item_id` on `user_card` enables fully manual cards with no external source.

## API and compatibility
- New responses emphasize `card`, optional `catalog`, and `provider`.
- Deprecated `film_*` / `film_id` fields remain on a transition window for legacy clients.

## Delivery phases (high level)
1. Schema + backfill + migration tests (counts, id preservation, FK integrity).
2. Backend reads with new DTOs + deprecated fields.
3. Backend writes: manual card, catalog-linked card, resolver path.
4. Frontend types and flows; detail/feed/profile use card-first UI.
5. Cleanup of legacy paths when clients have migrated.

## Verification
- Backend: Docker-backed `make backend-test` (migration invariants, API scenarios, resolver).
- Frontend: `npm run lint && npm run build`; manual create/view/profile checks.

## References
- Feature spec: `.cursor/features/abstract-user-cards/feature.md`
- Active plan: `.cursor/active/abstract-user-cards/plan.md`
- Read-only planning copy: `.cursor/plans/abstract-user-cards-v2_6f1f3132.plan.md`
