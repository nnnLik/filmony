# Catalog community page

## Scope
- `/catalog/:catalogItemId` community hub for games (RAWG) via `catalog_item_id`.
- Backend: `GET /api/catalog/items/{id}` + `community-cards`.
- Film `/films/:id` unchanged; film community delegates to shared list service.

## Acceptance criteria
- Game cards visible on catalog community page.
- CTAs: create card, watchlist, my card.
- Links from game card detail and create-card form.
- pytest + frontend lint/build pass.
