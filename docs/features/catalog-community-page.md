# Catalog community page

## Summary
Community hub for catalog items (games via RAWG) at `/catalog/:catalogItemId`, parity with film community pages.

## API
- `GET /api/catalog/items/{catalog_item_id}` — metadata + `my_card_id`
- `GET /api/catalog/items/{catalog_item_id}/community-cards` — paginated public ratings

Film endpoint `GET /api/films/{id}/community-cards` delegates to the shared list service (includes legacy `film_id`-only cards).

## UI
- **CatalogDetailPage**: poster, title, description, CTAs (rate / watchlist / my card), community list.
- **CommunityRatingsList**: shared component with `FilmDetailPage`.
- Links: game card detail «Все оценки →», create-card form when binding is `catalog_game`.

## Verification
```bash
make backend-test-one target=src/tests/api/test_catalog_community_routes.py
make backend-test-one target=src/tests/api/test_film_community_routes.py
cd frontend && npm run lint && npm run build
```
