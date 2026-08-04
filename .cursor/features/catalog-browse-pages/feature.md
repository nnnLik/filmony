# Catalog browse pages

## Scope
Community directors/genres index + profile genre drill-down.

## Acceptance
- `GET /api/directors` (paginated index), existing detail unchanged
- `GET /api/genres`, `/{slug}`, `/{slug}/films`; `genre_slug` helper
- `genre` query on user cards; `genre_distribution` in stats
- DirectorsIndexPage, GenresIndexPage, GenreDetailPage; profile entry links
- pytest: `test_catalog_browse_routes.py`
